class LZ77Compressor:

    @classmethod
    def _partial_kmp_search(cls, search_string, pattern, stop_after=2 ** 20,
                            min_match_length=3):
        """
        Custom version of the KMP algorithm that finds the longest partial match
        if no full match is found. Stops searching after a specified number of characters.

        :param search_string: The string to search within.
        :param pattern: The pattern to search for.
        :param stop_after: Stop searching after this many characters. Default is infinity.
        :return: A tuple (index of the match, length of the match).
        """
        n = len(search_string)
        m = len(pattern)

        # Preprocess the pattern to generate the KMP table
        table = cls._kmp_preprocess_pattern(pattern)

        i = 0  # Index in the pattern
        j = 0  # Index in the search string

        longest_match_length = 0
        longest_match_index = -1

        while j < n:
            if j - i >= stop_after:
                break

            if pattern[i] == search_string[j]:
                i += 1
                j += 1
                if i == m:  # Full match found
                    return j - i, i
            else:
                if i == 0:
                    j += 1
                else:
                    if i > longest_match_length:
                        longest_match_length = i
                        longest_match_index = j - i

                    i = table[i - 1]

        if longest_match_length >= min_match_length:
            return longest_match_index, longest_match_length
        return longest_match_index, 0

    @classmethod
    def _kmp_preprocess_pattern(cls, pattern):
        """
        Preprocess the pattern to generate the KMP skip table.

        :param pattern: The pattern to preprocess.
        :return: The skip table as a list of integers.
        """
        m = len(pattern)
        table = [0] * m

        i = 0  # Length of the previous longest prefix suffix
        j = 1  # Current index in the pattern

        while j < m:
            if pattern[i] == pattern[j]:
                i += 1
                table[j] = i
                j += 1
            elif i == 0:
                table[j] = 0
                j += 1
            else:
                i = table[i - 1]

        return table

    @classmethod
    def encode(cls, data):
        i = 0
        n = len(data)
        window_size = 2 ** 9
        lookahead_size = 257
        min_match_length = 3
        tokens = []

        while i < n:
            # Define the search window and lookahead buffer
            search_start = max(0, i - window_size)
            search_window = data[search_start:i]
            lookahead_buffer = data[i:i + lookahead_size]

            # Use partial KMP to find the longest match
            match_index, match_length = cls._partial_kmp_search(
                search_window,
                lookahead_buffer,
                min_match_length=min_match_length
            )

            if match_length > 0 and len(lookahead_buffer) >= min_match_length:
                # Match found
                distance = len(search_window) - match_index
                next_character = data[
                    i + match_length] if i + match_length < n else None
                tokens.append((distance, match_length, next_character))
                i += match_length + 1  # Move past the matched string and next character
            else:
                # No match found
                tokens.append((0, 0, data[i]))
                i += 1  # Move one character ahead

        return tokens

    @classmethod
    def decode(cls, tokens):
        data = b''
        for distance, length, next_character in tokens:
            if length > 0:
                start = len(data) - distance
                for j in range(length):
                    data += data[start + j].to_bytes()
            if next_character is not None:
                data += next_character.to_bytes()

        return data
