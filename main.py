import os

from compressors import DeflateCompressor

if __name__ == '__main__':
    for file in os.listdir('samples_test'):

        print(f'Compressing {file}')
        with open('samples_test/' + file, 'rb') as f:
            data = f.read()

        print(f'Original length: {len(data)} bytes')
        compressed_data = DeflateCompressor.compress(data)
        compressed_length = len(compressed_data) // 8

        print(f'Compressed length: {compressed_length} bytes')

        print('Asserting Decompression Consistency')
        assert DeflateCompressor.decompress(compressed_data) == data
        print('Done!')
