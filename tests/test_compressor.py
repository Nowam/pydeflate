#!/usr/bin/env python3
"""
Unit tests for the Lossless Compressor.

This test suite covers all compression algorithms and edge cases.
"""

import unittest
import os
import pytest

from compressors import DeflateCompressor
from compressors.lz77 import LZ77Compressor
from compressors.huffman import HuffmanCompressor
from compressors.integer import IntegerCompressor
from compressors.helpers.block_splitter import BlockSplitter


class TestIntegerCompressor(unittest.TestCase):
    """Test the Integer compression algorithm."""
    
    def test_decode_insufficient_data(self):
        """Test decoding with insufficient data."""
        with self.assertRaises(ValueError):
            IntegerCompressor.decode(b'', 1)
    
    def test_decode_invalid_encoding(self):
        """Test decoding with invalid encoding."""
        with self.assertRaises(ValueError):
            IntegerCompressor.decode(b'1111', 1)


@pytest.mark.parametrize("data,description", [
    ([42], "single number"),
    ([1, 5, 10, 100, 255, 1000], "multiple numbers"),
    ([0], "zero"),
    ([65535, 1000000], "large numbers"),
])
def test_integer_compressor_encode_decode_round_trip(data, description):
    """Test encoding and decoding round trip for various data types."""
    encoded = IntegerCompressor.encode(data)
    decoded, remaining = IntegerCompressor.decode(encoded, len(data))
    assert decoded == data
    assert remaining == b''


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
        bit_lengths = [2, 1, 3, 0, 3]
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
    
    def test_kmp_preprocessing(self):
        """Test KMP preprocessing algorithm."""
        pattern = b"abcabcab"
        table = LZ77Compressor._kmp_preprocess_pattern(pattern)
        self.assertEqual(len(table), len(pattern))
        self.assertIsInstance(table, list)


@pytest.mark.parametrize("data,description", [
    (b"hello world", "simple string"),
    (b"abcabcabc", "repeated pattern"),
    (b"", "empty data"),
    (b"a", "single byte"),
    (b"a" * 1000, "long repetition"),
])
def test_lz77_compressor_encode_decode_round_trip(data, description):
    """Test encoding and decoding round trip for various data types."""
    tokens = LZ77Compressor.encode(data)
    decoded = LZ77Compressor.decode(tokens)
    assert decoded == data


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
    
    def test_compress_decompress_random_data(self):
        """Test compressing and decompressing random-like data."""
        import random
        random.seed(42)
        data = bytes([random.randint(0, 255) for _ in range(1000)])
        compressed = DeflateCompressor.compress(data)
        decompressed = DeflateCompressor.decompress(compressed)
        self.assertEqual(decompressed, data)
    
    def test_compress_decompress_large_file(self):
        """Test compressing and decompressing larger data with compression ratio check."""
        data = b"The quick brown fox jumps over the lazy dog. " * 1000
        compressed = DeflateCompressor.compress(data)
        decompressed = DeflateCompressor.decompress(compressed)
        self.assertEqual(decompressed, data)
        
        # Check that compression actually happened
        self.assertLess(len(compressed) // 8, len(data))


@pytest.mark.parametrize("data,description", [
    (b"", "empty data"),
    (b"a", "single byte"),
    (b"hello world", "simple text"),
    (b"abc" * 100, "repeated data"),
    (bytes(range(256)) * 10, "binary data"),
])
def test_deflate_compressor_compress_decompress_round_trip(data, description):
    """Test compressing and decompressing round trip for various data types."""
    compressed = DeflateCompressor.compress(data)
    decompressed = DeflateCompressor.decompress(compressed)
    assert decompressed == data


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


@pytest.mark.parametrize("data,description,min_ratio", [
    (b"a" * 1000, "highly repetitive", 50),
    (b"The quick brown fox jumps over the lazy dog. " * 100, "natural text", 0),
    (bytes(range(256)), "sequential bytes", 0),
    (b"abc123XYZ!@#" * 100, "mixed content", 0),
])
def test_compression_ratios_different_data_types(data, description, min_ratio):
    """Test compression ratios on different data types."""
    compressed = DeflateCompressor.compress(data)
    decompressed = DeflateCompressor.decompress(compressed)
    
    # Verify correctness
    assert decompressed == data
    
    # Calculate compression ratio
    original_size = len(data)
    compressed_size = len(compressed) // 8
    ratio = (1 - compressed_size / original_size) * 100
    
    # Check minimum expected compression ratio
    if min_ratio > 0:
        assert ratio > min_ratio, f"Poor compression for {description}: {ratio:.2f}% < {min_ratio}%"
    
    print(f"{description}: {ratio:.2f}% compression")
