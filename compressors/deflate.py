from compressors.helpers.block_splitter import BlockSplitter
from compressors.huffman import HuffmanCompressor
from compressors.integer import IntegerCompressor
from compressors.lz77 import LZ77Compressor

FIXED_LENGTH_TO_CODE = {}
for i in range(0, 144):
    FIXED_LENGTH_TO_CODE[i] = format(i + 48, "#010b")[2:].encode()
for i in range(0, 112):
    FIXED_LENGTH_TO_CODE[i + 144] = format(i + 400, "#011b")[2:].encode()
for i in range(0, 24):
    FIXED_LENGTH_TO_CODE[256 + i] = format(i, "#09b")[2:].encode()
for i in range(0, 8):
    FIXED_LENGTH_TO_CODE[280 + i] = format(i + 192, "#010b")[2:].encode()

FIXED_CODE_TO_LENGTH = {v: k for k, v in FIXED_LENGTH_TO_CODE.items()}

FIXED_DISTANCE_TO_CODE = {i: format(i, "#07b")[2:].encode() for i in range(0, 32)}
FIXED_CODE_TO_DISTANCE = {v: k for k, v in FIXED_DISTANCE_TO_CODE.items()}


class SymbolLengthAlphabet:
    LENGTH_TABLE = [
        (3, 0),
        (4, 0),
        (5, 0),
        (6, 0),
        (7, 0),
        (8, 0),
        (9, 0),
        (10, 0),
        # Codes 257–264
        (11, 1),
        (13, 1),
        (15, 1),
        (17, 1),  # Codes 265–268
        (19, 2),
        (23, 2),
        (27, 2),
        (31, 2),  # Codes 269–272
        (35, 3),
        (43, 3),
        (51, 3),
        (59, 3),  # Codes 273–276
        (67, 4),
        (83, 4),
        (99, 4),
        (115, 4),  # Codes 277–280
        (131, 5),
        (163, 5),
        (195, 5),
        (227, 5),  # Codes 281–284
        (258, 0),  # Code 285
    ]

    @classmethod
    def decode(cls, symbol, extra_bits):
        """
        Decodes a symbol and extra bits into its literal/length representation.
        """
        if 0 <= symbol <= 255:
            # Literal symbol
            return symbol
        elif 257 <= symbol <= 285:
            # Decode length
            return cls.decode_length(symbol, extra_bits)
        else:
            raise ValueError("Invalid symbol for literal/length alphabet.")

    @classmethod
    def encode(cls, length):
        """
        Encodes the given length into a symbol and extra bits based on the deflate
        length table.
        Returns the symbol and a list of extra bits.
        """

        for i, (base, extra_bits) in enumerate(cls.LENGTH_TABLE):
            if base <= length < base + (1 << extra_bits):
                extra_value = length - base
                if extra_bits > 0:
                    extra_bits_encoded = f"{extra_value:0{extra_bits}b}"
                else:
                    extra_bits_encoded = ""
                return 257 + i, extra_bits_encoded.encode()

        raise ValueError("Invalid length value.")

    @classmethod
    def decode_length(cls, symbol, data):
        """
        Decodes a symbol and extra bits into the original length value.
        Consumes the required number of bits from the input data.
        """

        if not (257 <= symbol < 286):
            raise ValueError("Invalid length symbol.")

        base, extra_bits = cls.LENGTH_TABLE[symbol - 257]

        # Read the required number of extra bits
        extra_value = 0
        if extra_bits > 0:
            extra_bits_str = data[:extra_bits]
            extra_value = int(extra_bits_str, 2)

        # Calculate the decoded length
        return base + extra_value, data[extra_bits:]


class DistanceAlphabet:
    DISTANCE_TABLE = [
        (1, 0),
        (2, 0),
        (3, 0),
        (4, 0),  # Codes 0–3
        (5, 1),
        (7, 1),  # Codes 4–5
        (9, 2),
        (13, 2),  # Codes 6–7
        (17, 3),
        (25, 3),  # Codes 8–9
        (33, 4),
        (49, 4),  # Codes 10–11
        (65, 5),
        (97, 5),  # Codes 12–13
        (129, 6),
        (193, 6),  # Codes 14–15
        (257, 7),
        (385, 7),  # Codes 16–17
        (513, 8),
        (769, 8),  # Codes 18–19
        (1025, 9),
        (1537, 9),  # Codes 20–21
        (2049, 10),
        (3073, 10),  # Codes 22–23
        (4097, 11),
        (6145, 11),  # Codes 24–25
        (8193, 12),
        (12289, 12),  # Codes 26–27
        (16385, 13),
        (24577, 13),  # Codes 28–29
    ]

    @classmethod
    def encode(cls, distance):
        """
        Encodes a distance into the distance alphabet format.
        """
        distance_symbol, extra_value, extra_bits = cls.encode_distance(distance)
        # convert to bin with leading zeros up to extra bits
        if extra_bits > 0:
            extra_value = bin(extra_value)[2:].zfill(extra_bits)
        else:
            extra_value = ""
        return distance_symbol, extra_value.encode()

    @classmethod
    def decode(cls, symbol, extra_bits):
        """
        Decodes a symbol and extra bits into its distance representation.
        """
        return cls.decode_distance(symbol, extra_bits)

    @classmethod
    def encode_distance(cls, distance):
        """
        Encodes the given distance into a symbol and extra bits based on the provided
        table.
        Returns the symbol and a list of extra bits.
        """

        for code, (base, extra_bits) in enumerate(cls.DISTANCE_TABLE):
            if base <= distance < base + (1 << extra_bits):
                # Calculate the extra bits value
                extra_value = distance - base
                return code, extra_value, extra_bits

        raise ValueError("Invalid distance value.")

    @classmethod
    def decode_distance(cls, symbol, data):
        """
        Decodes a symbol and extra bits into the original distance value.
        Consumes the required number of bits from the input data.
        """

        if not (0 <= symbol < len(cls.DISTANCE_TABLE)):
            raise ValueError("Invalid distance symbol.")

        base, extra_bits = cls.DISTANCE_TABLE[symbol]
        # Read the required number of extra bits
        extra_value = 0
        if extra_bits > 0:
            extra_bits_str = data[:extra_bits]
            extra_value = int(extra_bits_str, 2)

        # Calculate the decoded distance
        return base + extra_value, data[extra_bits:]


def binary_string_to_bytes(binary_string: bytes) -> bytes:
    """Convert binary string like b'01001100' to actual bytes with padding info."""
    binary_str = binary_string.decode("ascii")

    # Store original length and pad to byte boundary
    original_length = len(binary_str)
    padding = (8 - (original_length % 8)) % 8
    binary_str += "0" * padding

    # Encode original length as first 4 bytes (32-bit unsigned integer)
    result = bytearray()
    result.extend(original_length.to_bytes(4, "big"))

    # Convert binary string to bytes
    for i in range(0, len(binary_str), 8):
        byte_str = binary_str[i : i + 8]
        result.append(int(byte_str, 2))

    return bytes(result)


def bytes_to_binary_string(data: bytes) -> bytes:
    """Convert bytes back to binary string for decompression."""
    # Read original length from first 4 bytes
    original_length = int.from_bytes(data[:4], "big")

    # Convert remaining bytes to binary string
    binary_str = "".join(format(byte, "08b") for byte in data[4:])

    # Truncate to original length
    binary_str = binary_str[:original_length]

    return binary_str.encode("ascii")


class DeflateCompressor:
    @classmethod
    def compress(cls, data: bytes) -> bytes:
        """
        For each block of size 32KB, compress it using one of 3 options.
        Block headers:
            00 - no compression
            01 - compressed with fixed Huffman codes
            10 - compressed with dynamic Huffman codes
            11 - reserved (error)
        :param data:
        :return:
        """
        # Split the data into blocks of 32KB
        tokens = LZ77Compressor.encode(data)
        splitter = BlockSplitter()
        blocks = []
        current_block = []

        pos = 0
        while pos < len(tokens):
            token = tokens[pos]

            # Observe the token based on its type
            if token[0] == 0:  # Literal
                splitter.observe_literal(token[2])
            else:  # Match
                splitter.observe_match(token[1])

            # Add token to current block
            current_block.append(token)

            # Check if we should end the current block
            if splitter.should_end_block(len(current_block)):
                # Store the current block
                blocks.append(current_block)

                # Start a new block
                current_block = []
                splitter.reset()

            pos += 1

        # Don't forget the last block
        if current_block:
            blocks.append(current_block)
        res = b""
        for block_tokens in blocks:
            # add block header based on: 00 - no compression, 01 - fixed, 10 - dynamic
            literal_length_distance_pairs = []
            # Encode each (distance, length, symbol) tuple into Deflate alphabets
            for distance, length, symbol in block_tokens:
                if distance != 0:
                    # Encode lengths and distances
                    length_symbol, length_extra_value = SymbolLengthAlphabet.encode(
                        length
                    )
                    distance_symbol, distance_extra_value = DistanceAlphabet.encode(
                        distance
                    )
                    literal_length_distance_pairs.append(
                        (
                            length_symbol,
                            length_extra_value,
                            distance_symbol,
                            distance_extra_value,
                        )
                    )
                if symbol is not None:
                    # Encode literals directly
                    literal_length_distance_pairs.append((symbol, None, None, None))
            # add end
            literal_length_distance_pairs.append((256, None, None, None))
            res_dynamic = b""
            # Compress the literal/length and distance symbols using separate Huffman
            # codes
            literal_length_bit_lengths, literal_length_code = (
                HuffmanCompressor.create_codes(
                    [t[0] for t in literal_length_distance_pairs], alphabet_length=286
                )
            )
            distance_bit_lengths, distance_code = HuffmanCompressor.create_codes(
                [t[2] for t in literal_length_distance_pairs if t[2] is not None],
                alphabet_length=30,
            )
            # write the trees, compressed literal/length and distance
            res_dynamic += IntegerCompressor.encode(
                [*literal_length_bit_lengths, *distance_bit_lengths]
            )
            for (
                literal_length,
                literal_length_extra_value,
                distance,
                distance_extra_value,
            ) in literal_length_distance_pairs:
                res_dynamic += literal_length_code[literal_length]
                if literal_length_extra_value is not None:
                    res_dynamic += literal_length_extra_value
                if distance is not None:
                    res_dynamic += distance_code[distance]
                    res_dynamic += distance_extra_value
            res_fixed = b""
            # Compress with fixed codes
            for (
                literal_length,
                literal_length_extra_value,
                distance,
                distance_extra_value,
            ) in literal_length_distance_pairs:
                res_fixed += FIXED_LENGTH_TO_CODE[literal_length]
                if literal_length_extra_value is not None:
                    res_fixed += literal_length_extra_value
                if distance is not None:
                    res_fixed += FIXED_DISTANCE_TO_CODE[distance]
                    res_fixed += distance_extra_value

            if len(res_dynamic) > len(res_fixed):
                res += b"01" + res_fixed
            else:
                res += b"10" + res_dynamic
        return binary_string_to_bytes(res)

    @classmethod
    def decompress(cls, data: bytes) -> bytes:
        # Convert bytes back to binary string format for processing
        data = bytes_to_binary_string(data)
        tokens = []
        while data:
            # Read block header
            block_header, data = data[:2], data[2:]
            if block_header == b"10":
                length_literal_bit_lengths, data = IntegerCompressor.decode(data, 286)
                distance_bit_lengths, data = IntegerCompressor.decode(data, 30)
                # Decompress using Huffman trees
                length_literal_code = HuffmanCompressor.generate_decode_table(
                    length_literal_bit_lengths
                )
                distance_code = HuffmanCompressor.generate_decode_table(
                    distance_bit_lengths
                )
            else:  # block_header == b'01':
                length_literal_code = FIXED_CODE_TO_LENGTH
                distance_code = FIXED_CODE_TO_DISTANCE
            """
            loop (until end of block code recognized)
                         decode literal/length value from input stream
                         if value < 256
                            copy value (literal byte) to output stream
                         otherwise
                            if value = end of block (256)
                               break from loop
                            otherwise (value = 257..285)
                               decode distance from input stream
                      end loop
            """
            while True:
                literal_length, data = HuffmanCompressor.decode_next(
                    data, length_literal_code
                )
                if literal_length < 256:
                    tokens.append((0, 0, literal_length))
                elif literal_length == 256:
                    break
                else:
                    # format is length, distance, literal
                    length, data = SymbolLengthAlphabet.decode(literal_length, data)
                    distance_symbol, data = HuffmanCompressor.decode_next(
                        data, distance_code
                    )
                    distance, data = DistanceAlphabet.decode(distance_symbol, data)
                    literal, data = HuffmanCompressor.decode_next(
                        data, length_literal_code
                    )
                    if literal == 256:
                        tokens.append((distance, length, None))
                        break
                    tokens.append((distance, length, literal))
        return LZ77Compressor.decode(tokens)
