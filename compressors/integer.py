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
            if not data:
                raise ValueError("Insufficient data to decode integer")
            
            num = 0
            while num < len(data) and data[num] == 49:
                num += 1
            
            if num >= len(data):
                raise ValueError("Invalid integer encoding: no terminator found")
            
            end_pos = num * 2 + 1
            if end_pos > len(data):
                raise ValueError("Invalid integer encoding: insufficient data")
            
            binary_str = data[num + 1:end_pos].decode()
            if not binary_str:
                decoded_int = 0
            else:
                decoded_int = int(binary_str, 2)
            
            data = data[end_pos:]
            decoded_numbers.append(decoded_int)
            if len(decoded_numbers) == length:
                break
        return decoded_numbers, data

