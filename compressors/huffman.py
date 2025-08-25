from collections import Counter
from heapq import heappop, heappush

ALPHABET = [i for i in range(2**16)]


class HuffmanCompressor:
    FIXED_BYTE_TO_CODE = {}
    FIXED_CODE_TO_BYTE = {}

    def __init__(self):
        super().__init__()

    @classmethod
    def _calculate_empirical_frequency(cls, data: list[int]):
        return Counter(data)

    @classmethod
    def _create_huffman_tree(cls, frequencies):
        if len(frequencies) == 1:
            (letter,) = frequencies
            return {letter: 1}

        queue = []
        res = dict.fromkeys(frequencies, 0)
        for letter, frequency in frequencies.items():
            heappush(queue, (frequency, tuple([letter])))
        while len(queue) > 1:
            first_freq, first_letters = heappop(queue)
            second_freq, second_letters = heappop(queue)
            for letter in first_letters:
                res[letter] = 1 + res[letter]

            for letter in second_letters:
                res[letter] = 1 + res[letter]

            heappush(
                queue, (first_freq + second_freq, (*first_letters, *second_letters))
            )

        return res

    @classmethod
    def generate_dynamic_huffman_codes(cls, bit_lengths):
        """
        Generate Huffman codes based on the bit lengths using the Deflate algorithm.
        """
        if not bit_lengths or max(bit_lengths) == 0:
            return {}

        # Step 1: Count the number of codes for each bit length
        max_bits = max(bit_lengths)
        bl_count = [0] * (max_bits + 1)
        for length in bit_lengths:
            if length > 0:
                bl_count[length] += 1

        # Step 2: Compute the smallest code for each bit length
        next_code = [0] * (max_bits + 1)
        code = 0
        for bits in range(1, max_bits + 1):
            code <<= 1
            next_code[bits] = code
            code += bl_count[bits]

        # Step 3: Assign codes to symbols
        codes = {}
        for i in range(len(bit_lengths)):
            length = bit_lengths[i]
            if length > 0:
                codes[i] = f"{next_code[length]:0{length}b}".encode()
                next_code[length] += 1

        return codes

    @classmethod
    def generate_decode_table(cls, bit_lengths):
        """
        Generate a decoding table for reverse mapping from codes to symbols.
        """
        codes = cls.generate_dynamic_huffman_codes(bit_lengths)
        decode_table = {}
        for symbol, code in codes.items():
            decode_table[code] = symbol
        return decode_table

    @classmethod
    def encode(cls, data, alphabet_length=len(ALPHABET), compress_counts=False):
        code_lengths = cls._create_huffman_tree(
            cls._calculate_empirical_frequency(data)
        )
        code_lengths = [
            code_lengths[letter] if letter in code_lengths else 0
            for letter in range(alphabet_length)
        ]
        codes = {
            letter: code
            for code, letter in cls.generate_decode_table(code_lengths).items()
        }  # todo: fix
        # convert series of 0s to two numbers
        zero_count = 0
        code_lengths_compact = []
        for i, length in enumerate(code_lengths):
            if length == 0 and i < len(code_lengths) - 1:
                zero_count += 1
            else:
                if zero_count > 0:
                    code_lengths_compact.append(0)
                    if length == 0:
                        zero_count += 1
                    code_lengths_compact.append(zero_count)
                    zero_count = 0
                if length != 0:
                    code_lengths_compact.append(length)

        code_lengths_compact.append(1024)
        encoded_data = [codes[letter] for letter in data]
        return code_lengths, encoded_data

    @classmethod
    def create_codes(cls, data, alphabet_length):
        code_lengths = cls._create_huffman_tree(
            cls._calculate_empirical_frequency(data)
        )
        code_lengths = [
            code_lengths[letter] if letter in code_lengths else 0
            for letter in range(alphabet_length)
        ]
        codes = {
            letter: code
            for code, letter in cls.generate_decode_table(code_lengths).items()
        }  # todo: fix
        return code_lengths, codes

    @classmethod
    def decode(cls, data, bit_lengths):
        decode_table = cls.generate_decode_table(bit_lengths)
        current_bits = ""
        decoded_message = []
        for bit in data:
            current_bits += bit
            if current_bits in decode_table:
                decoded_message.append(decode_table[current_bits])
                current_bits = ""  # Reset current bits for the next symbol
        return decoded_message

    @classmethod
    def decode_next(cls, data, code):
        current_bits = b""
        for i, bit_char in enumerate(data):
            current_bits += bytes([bit_char])
            if current_bits in code:
                return code[current_bits], data[i + 1 :]
        raise ValueError("No valid Huffman code found in data")
