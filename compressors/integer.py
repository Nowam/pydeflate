class IntegerCompressor:

    @classmethod
    def encode(cls, data: list[int]) -> bytes:
        encoded_numbers = b''
        for num in data:
            binary_number = bin(num)[2:]
            encoded_numbers += b'1' * len(binary_number) + b'0' + binary_number.encode()
        return encoded_numbers

    @classmethod
    def decode(cls, data: bytes, length: int) -> tuple[list[int], bytes]:
        decoded_numbers = []
        while True:
            num = 0
            while data[num] == 49:
                num += 1
            decoded_int = int(data[num + 1:num * 2 + 1], 2)
            data = data[num * 2 + 1:]
            decoded_numbers.append(decoded_int)
            if len(decoded_numbers) == length:
                break
        return decoded_numbers, data

