#!/usr/bin/env python3
"""
Lossless Compressor - A DEFLATE implementation for data compression.

This tool provides lossless compression and decompression using the DEFLATE algorithm,
which combines LZ77 and Huffman coding for efficient data reduction.
"""

import argparse
import sys
import time
from pathlib import Path
from typing import Optional

from compressors import DeflateCompressor


def compress_data(data: bytes) -> bytes:
    """Compress data using DEFLATE algorithm and return compressed bytes."""
    return DeflateCompressor.compress(data)


def compress_file(input_path: Path, output_path: Optional[Path] = None) -> bytes:
    """Compress a file using DEFLATE algorithm and return compressed bytes."""
    if not input_path.exists():
        print(f"Error: Input file '{input_path}' does not exist.", file=sys.stderr)
        sys.exit(1)
    
    if not input_path.is_file():
        print(f"Error: '{input_path}' is not a file.", file=sys.stderr)
        sys.exit(1)
    
    try:
        print(f"Compressing '{input_path}'...")
        start_time = time.time()
        
        with open(input_path, 'rb') as f:
            data = f.read()
        
        original_size = len(data)
        print(f"Original size: {original_size:,} bytes")
        
        compressed_data = DeflateCompressor.compress(data)
        compressed_size = len(compressed_data)
        
        elapsed_time = time.time() - start_time
        compression_ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
        
        print(f"Compressed size: {compressed_size:,} bytes")
        print(f"Compression ratio: {compression_ratio:.2f}%")
        print(f"Compression time: {elapsed_time:.2f} seconds")
        
        # Optionally save to file if output_path is provided
        if output_path is not None:
            if output_path is True:  # Use default path
                output_path = input_path.with_suffix(input_path.suffix + '.deflate')
            with open(output_path, 'wb') as f:
                f.write(compressed_data)
            print(f"Output saved to: '{output_path}'")
        
        return compressed_data
        
    except Exception as e:
        print(f"Error during compression: {e}", file=sys.stderr)
        sys.exit(1)


def decompress_file(input_path: Path, output_path: Optional[Path] = None) -> None:
    """Decompress a file using DEFLATE algorithm."""
    if not input_path.exists():
        print(f"Error: Input file '{input_path}' does not exist.", file=sys.stderr)
        sys.exit(1)
    
    if not input_path.is_file():
        print(f"Error: '{input_path}' is not a file.", file=sys.stderr)
        sys.exit(1)
    
    # Default output path
    if output_path is None:
        if input_path.suffix == '.deflate':
            output_path = input_path.with_suffix('')
        else:
            output_path = input_path.with_suffix('.decompressed')
    
    try:
        print(f"Decompressing '{input_path}'...")
        start_time = time.time()
        
        with open(input_path, 'rb') as f:
            compressed_data = f.read()
        
        compressed_size = len(compressed_data)
        print(f"Compressed size: {compressed_size:,} bytes")
        
        decompressed_data = DeflateCompressor.decompress(compressed_data)
        decompressed_size = len(decompressed_data)
        
        with open(output_path, 'wb') as f:
            f.write(decompressed_data)
        
        elapsed_time = time.time() - start_time
        
        print(f"Decompressed size: {decompressed_size:,} bytes")
        print(f"Decompression time: {elapsed_time:.2f} seconds")
        print(f"Output saved to: '{output_path}'")
        
    except Exception as e:
        print(f"Error during decompression: {e}", file=sys.stderr)
        sys.exit(1)


def test_round_trip(input_path: Path) -> None:
    """Test compression and decompression round-trip consistency."""
    if not input_path.exists():
        print(f"Error: Input file '{input_path}' does not exist.", file=sys.stderr)
        sys.exit(1)
    
    try:
        print(f"Testing round-trip for '{input_path}'...")
        
        with open(input_path, 'rb') as f:
            original_data = f.read()
        
        print(f"Original size: {len(original_data):,} bytes")
        
        # Compress
        compressed_data = DeflateCompressor.compress(original_data)
        compressed_size = len(compressed_data)
        print(f"Compressed size: {compressed_size:,} bytes")
        
        # Decompress
        decompressed_data = DeflateCompressor.decompress(compressed_data)
        
        # Verify
        if original_data == decompressed_data:
            print("✓ Round-trip test PASSED - Data integrity preserved")
            compression_ratio = (1 - compressed_size / len(original_data)) * 100
            print(f"Compression ratio: {compression_ratio:.2f}%")
        else:
            print("✗ Round-trip test FAILED - Data corruption detected", file=sys.stderr)
            sys.exit(1)
            
    except Exception as e:
        print(f"Error during round-trip test: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point for the compressor CLI."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Compress command
    compress_parser = subparsers.add_parser('compress', help='Compress a file')
    compress_parser.add_argument('input', type=Path, help='Input file to compress')
    compress_parser.add_argument('-o', '--output', type=Path, help='Output compressed file (default: input + .deflate)')
    
    # Decompress command
    decompress_parser = subparsers.add_parser('decompress', help='Decompress a file')
    decompress_parser.add_argument('input', type=Path, help='Input file to decompress')
    decompress_parser.add_argument('-o', '--output', type=Path, help='Output decompressed file (default: remove .deflate extension)')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test compression round-trip on a file')
    test_parser.add_argument('input', type=Path, help='Input file to test')
    
    # Parse arguments
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    # Execute command
    if args.command == 'compress':
        compress_file(args.input, args.output)
    elif args.command == 'decompress':
        decompress_file(args.input, args.output)
    elif args.command == 'test':
        test_round_trip(args.input)


if __name__ == '__main__':
    main()
