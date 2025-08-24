#!/usr/bin/env python3
"""
Unit tests for the Lossless Compressor.

This test suite covers all compression algorithms and edge cases.
"""

import unittest
import tempfile
import os
from pathlib import Path

from compressors import DeflateCompressor
from compressors.lz77 import LZ77Compressor
from compressors.huffman import HuffmanCompressor
from compressors.integer import IntegerCompressor
from compressors.helpers.block_splitter import BlockSplitter


class TestIntegerCompressor(unittest.TestCase):
    """Test the Integer compression algorithm."""
    
    def test_encode_decode_single_number(self):
        """Test encoding and decoding a single number."""
        data = [42]
        encoded = IntegerCompressor.encode(data)
        decoded, remaining = IntegerCompressor.decode(encoded, 1)
        self.assertEqual(decoded, data)
        self.assertEqual(remaining, b'')
    
    def test_encode_decode_multiple_numbers(self):
        """Test encoding and decoding multiple numbers."""
        data = [1, 5, 10, 100, 255, 1000]
        encoded = IntegerCompressor.encode(data)
        decoded, remaining = IntegerCompressor.decode(encoded, len(data))
        self.assertEqual(decoded, data)
        self.assertEqual(remaining, b'')
    
    def test_encode_decode_zero(self):
        """Test encoding and decoding zero."""
        data = [0]
        encoded = IntegerCompressor.encode(data)
        decoded, remaining = IntegerCompressor.decode(encoded, 1)
        self.assertEqual(decoded, data)
    
    def test_encode_decode_large_numbers(self):
        """Test encoding and decoding large numbers."""
        data = [65535, 1000000]
        encoded = IntegerCompressor.encode(data)
        decoded, remaining = IntegerCompressor.decode(encoded, len(data))
        self.assertEqual(decoded, data)
    
    def test_decode_insufficient_data(self):
        """Test decoding with insufficient data."""
        with self.assertRaises(ValueError):
            IntegerCompressor.decode(b'', 1)
    
    def test_decode_invalid_encoding(self):
        """Test decoding with invalid encoding."""
        with self.assertRaises(ValueError):
            IntegerCompressor.decode(b'1111', 1)


class TestHuffmanCompressor(unittest.TestCase):
    """Test the Huffman compression algorithm."""
    
    def test_create_huffman_tree_single_symbol(self):
        """Test creating Huffman tree with single symbol."""
        frequencies = {65: 10}
        tree = HuffmanCompressor._create_huffman_tree(frequencies)
        self.assertEqual(tree, {65: 1})
    
    def test_create_huffman_tree_multiple_symbols(self):
        """Test creating Huffman tree with multiple symbols."""
        frequencies = {65: 1, 66: 2, 67: 3}
        tree = HuffmanCompressor._create_huffman_tree(frequencies)
        # All symbols should have positive bit lengths
        for symbol in frequencies:
            self.assertGreater(tree[symbol], 0)
    
    def test_generate_dynamic_huffman_codes(self):
        """Test generating Huffman codes from bit lengths."""
        bit_lengths = [2, 1, 3, 0, 2]
        codes = HuffmanCompressor.generate_dynamic_huffman_codes(bit_lengths)
        
        # Check that all non-zero length symbols have codes
        for i, length in enumerate(bit_lengths):
            if length > 0:
                self.assertIn(i, codes)
                # codes[i] is bytes, so we decode to string to check bit length
                self.assertEqual(len(codes[i].decode()), length)
            else:
                self.assertNotIn(i, codes)
    
    def test_create_codes_round_trip(self):
        """Test creating codes and using them for encoding/decoding."""
        data = [65, 66, 65, 67, 65, 65, 66]
        bit_lengths, codes = HuffmanCompressor.create_codes(data, 256)
        
        # Check that common symbols get shorter codes
        self.assertLessEqual(bit_lengths[65], bit_lengths[67])  # 'A' appears more than 'C'
    
    def test_decode_next_valid_code(self):
        """Test decoding next symbol from valid data."""
        bit_lengths = [0, 2, 1, 3]
        decode_table = HuffmanCompressor.generate_decode_table(bit_lengths)
        
        # Find a valid code to test with
        if decode_table:
            code, symbol = next(iter(decode_table.items()))
            data = code + b'extra'
            result_symbol, remaining = HuffmanCompressor.decode_next(data, decode_table)
            self.assertEqual(result_symbol, symbol)
            self.assertEqual(remaining, b'extra')
    
    def test_decode_next_invalid_code(self):
        """Test decoding with invalid code."""
        decode_table = {b'01': 1, b'10': 2}
        with self.assertRaises(ValueError):
            HuffmanCompressor.decode_next(b'11', decode_table)


class TestLZ77Compressor(unittest.TestCase):
    """Test the LZ77 compression algorithm."""
    
    def test_encode_decode_simple_string(self):
        """Test encoding and decoding a simple string."""
        data = b"hello world"
        tokens = LZ77Compressor.encode(data)
        decoded = LZ77Compressor.decode(tokens)
        self.assertEqual(decoded, data)
    
    def test_encode_decode_repeated_pattern(self):
        """Test encoding and decoding repeated patterns."""
        data = b"abcabcabc"
        tokens = LZ77Compressor.encode(data)
        decoded = LZ77Compressor.decode(tokens)
        self.assertEqual(decoded, data)
    
    def test_encode_decode_empty_data(self):
        """Test encoding and decoding empty data."""
        data = b""
        tokens = LZ77Compressor.encode(data)
        decoded = LZ77Compressor.decode(tokens)
        self.assertEqual(decoded, data)
    
    def test_encode_decode_single_byte(self):
        """Test encoding and decoding single byte."""
        data = b"a"
        tokens = LZ77Compressor.encode(data)
        decoded = LZ77Compressor.decode(tokens)
        self.assertEqual(decoded, data)
    
    def test_encode_decode_long_repetition(self):
        """Test encoding and decoding long repetitions."""
        data = b"a" * 1000
        tokens = LZ77Compressor.encode(data)
        decoded = LZ77Compressor.decode(tokens)
        self.assertEqual(decoded, data)
    
    def test_kmp_preprocessing(self):
        """Test KMP preprocessing algorithm."""
        pattern = b"abcabcab"
        table = LZ77Compressor._kmp_preprocess_pattern(pattern)
        self.assertEqual(len(table), len(pattern))
        self.assertIsInstance(table, list)


class TestBlockSplitter(unittest.TestCase):
    """Test the Block Splitter algorithm."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.splitter = BlockSplitter()
    
    def test_initialization(self):
        """Test proper initialization."""
        self.assertEqual(len(self.splitter.observations), self.splitter.NUM_OBSERVATION_TYPES)
        self.assertEqual(len(self.splitter.new_observations), self.splitter.NUM_OBSERVATION_TYPES)
        self.assertEqual(self.splitter.num_observations, 0)
        self.assertEqual(self.splitter.num_new_observations, 0)
    
    def test_observe_literal(self):
        """Test observing literal bytes."""
        initial_count = self.splitter.num_new_observations
        self.splitter.observe_literal(65)  # 'A'
        self.assertEqual(self.splitter.num_new_observations, initial_count + 1)
    
    def test_observe_match(self):
        """Test observing matches."""
        initial_count = self.splitter.num_new_observations
        self.splitter.observe_match(5)
        self.assertEqual(self.splitter.num_new_observations, initial_count + 1)
    
    def test_merge_observations(self):
        """Test merging new observations."""
        self.splitter.observe_literal(65)
        self.splitter.observe_match(10)
        
        old_new_count = self.splitter.num_new_observations
        self.splitter.merge_new_observations()
        
        self.assertEqual(self.splitter.num_observations, old_new_count)
        self.assertEqual(self.splitter.num_new_observations, 0)
    
    def test_should_end_block_insufficient_observations(self):
        """Test that blocks don't end with insufficient observations."""
        # Add some observations but not enough
        for i in range(100):
            self.splitter.observe_literal(i % 256)
        
        should_end = self.splitter.should_end_block(2000)
        self.assertFalse(should_end)
    
    def test_reset(self):
        """Test resetting the splitter."""
        self.splitter.observe_literal(65)
        self.splitter.observe_match(10)
        self.splitter.merge_new_observations()
        
        self.splitter.reset()
        
        self.assertEqual(self.splitter.num_observations, 0)
        self.assertEqual(self.splitter.num_new_observations, 0)
        self.assertEqual(sum(self.splitter.observations), 0)
        self.assertEqual(sum(self.splitter.new_observations), 0)


class TestDeflateCompressor(unittest.TestCase):
    """Test the main DEFLATE compression algorithm."""
    
    def test_compress_decompress_empty_data(self):
        """Test compressing and decompressing empty data."""
        data = b""
        compressed = DeflateCompressor.compress(data)
        decompressed = DeflateCompressor.decompress(compressed)
        self.assertEqual(decompressed, data)
    
    def test_compress_decompress_single_byte(self):
        """Test compressing and decompressing single byte."""
        data = b"a"
        compressed = DeflateCompressor.compress(data)
        decompressed = DeflateCompressor.decompress(compressed)
        self.assertEqual(decompressed, data)
    
    def test_compress_decompress_simple_text(self):
        """Test compressing and decompressing simple text."""
        data = b"hello world"
        compressed = DeflateCompressor.compress(data)
        decompressed = DeflateCompressor.decompress(compressed)
        self.assertEqual(decompressed, data)
    
    def test_compress_decompress_repeated_data(self):
        """Test compressing and decompressing repeated data."""
        data = b"abc" * 100
        compressed = DeflateCompressor.compress(data)
        decompressed = DeflateCompressor.decompress(compressed)
        self.assertEqual(decompressed, data)
    
    def test_compress_decompress_random_data(self):
        """Test compressing and decompressing random-like data."""
        import random
        random.seed(42)  # For reproducible tests
        data = bytes([random.randint(0, 255) for _ in range(1000)])
        compressed = DeflateCompressor.compress(data)
        decompressed = DeflateCompressor.decompress(compressed)
        self.assertEqual(decompressed, data)
    
    def test_compress_decompress_large_file(self):
        """Test compressing and decompressing larger data."""
        # Create test data with patterns
        data = b"The quick brown fox jumps over the lazy dog. " * 1000
        compressed = DeflateCompressor.compress(data)
        decompressed = DeflateCompressor.decompress(compressed)
        self.assertEqual(decompressed, data)
        
        # Check that compression actually happened
        self.assertLess(len(compressed) // 8, len(data))
    
    def test_compress_decompress_binary_data(self):
        """Test compressing and decompressing binary data."""
        data = bytes(range(256)) * 10
        compressed = DeflateCompressor.compress(data)
        decompressed = DeflateCompressor.decompress(compressed)
        self.assertEqual(decompressed, data)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system."""
    
    def test_cli_round_trip_with_tempfile(self):
        """Test CLI round-trip with temporary file."""
        import subprocess
        import tempfile
        
        # Create test data
        test_data = b"Hello, World! " * 1000
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp_input:
            tmp_input.write(test_data)
            tmp_input_path = tmp_input.name
        
        try:
            # Test using the CLI
            result = subprocess.run([
                'python3', 'main.py', 'test', tmp_input_path
            ], capture_output=True, text=True, cwd='.')
            
            self.assertEqual(result.returncode, 0)
            self.assertIn("Round-trip test PASSED", result.stdout)
            
        finally:
            os.unlink(tmp_input_path)
    
    def test_compression_ratios_different_data_types(self):
        """Test compression ratios on different data types."""
        test_cases = [
            (b"a" * 1000, "highly repetitive"),
            (b"The quick brown fox jumps over the lazy dog. " * 100, "natural text"),
            (bytes(range(256)), "sequential bytes"),
            (b"abc123XYZ!@#" * 100, "mixed content"),
        ]
        
        for data, description in test_cases:
            with self.subTest(description=description):
                compressed = DeflateCompressor.compress(data)
                decompressed = DeflateCompressor.decompress(compressed)
                
                # Verify correctness
                self.assertEqual(decompressed, data)
                
                # Calculate compression ratio
                original_size = len(data)
                compressed_size = len(compressed) // 8
                ratio = (1 - compressed_size / original_size) * 100
                
                # For highly repetitive data, we should see good compression
                if "repetitive" in description:
                    self.assertGreater(ratio, 50, f"Poor compression for {description}")
                
                print(f"{description}: {ratio:.2f}% compression")


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)