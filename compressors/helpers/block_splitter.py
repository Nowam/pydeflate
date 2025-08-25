class BlockSplitter:
    """
    A Python implementation of libdeflate's block splitting algorithm for DEFLATE
    compression.
    The algorithm decides when to start a new block with new Huffman codes by comparing
    symbol distribution patterns.
    """

    # Constants from the original implementation
    NUM_LITERAL_OBSERVATION_TYPES = 8  # 3 bits total: 2 high bits + 1 low bit
    NUM_MATCH_OBSERVATION_TYPES = 2  # short vs long match
    NUM_OBSERVATION_TYPES = NUM_LITERAL_OBSERVATION_TYPES + NUM_MATCH_OBSERVATION_TYPES
    NUM_OBSERVATIONS_PER_BLOCK_CHECK = 512
    MIN_BLOCK_LENGTH = 1000

    def __init__(self):
        # Initialize statistics
        self.observations = [0] * self.NUM_OBSERVATION_TYPES
        self.new_observations = [0] * self.NUM_OBSERVATION_TYPES
        self.num_observations = 0
        self.num_new_observations = 0

    def observe_literal(self, literal: int) -> None:
        """Record an observation of a literal byte."""
        # Use top 2 bits and low 1 bit of the literal (same heuristic as original)
        obs_type = ((literal >> 5) & 0x6) | (literal & 1)
        self.new_observations[obs_type] += 1
        self.num_new_observations += 1

    def observe_match(self, length: int) -> None:
        """Record an observation of a match."""
        # One type for "short match", one for "long match"
        obs_type = self.NUM_LITERAL_OBSERVATION_TYPES + (1 if length >= 9 else 0)
        self.new_observations[obs_type] += 1
        self.num_new_observations += 1

    def merge_new_observations(self) -> None:
        """Merge new observations into the cumulative counts."""
        for i in range(self.NUM_OBSERVATION_TYPES):
            self.observations[i] += self.new_observations[i]
            self.new_observations[i] = 0
        self.num_observations += self.num_new_observations
        self.num_new_observations = 0

    def should_end_block(self, block_length: int) -> bool:
        """
        Determine if it's time to end the current block based on symbol distribution
        changes and block length.
        """
        # First check if we have enough observations
        if (
            self.num_new_observations < self.NUM_OBSERVATIONS_PER_BLOCK_CHECK
            or block_length < self.MIN_BLOCK_LENGTH
        ):
            return False

        if self.num_observations == 0:
            self.merge_new_observations()
            return False

        # Calculate the sum of absolute differences in symbol probabilities
        total_delta = 0
        for i in range(self.NUM_OBSERVATION_TYPES):
            expected = self.observations[i] * self.num_new_observations
            actual = self.new_observations[i] * self.num_observations
            delta = abs(actual - expected)
            total_delta += delta

        num_items = self.num_observations + self.num_new_observations

        # Cutoff calculation (equivalent to 200/512 probability difference)
        cutoff = self.num_new_observations * 200 * self.num_observations // 512

        # Add penalty for very short blocks
        if block_length < 10000 and num_items < 8192:
            cutoff += (cutoff * (8192 - num_items)) // 8192

        # Add length-dependent penalty
        length_penalty = (block_length // 4096) * self.num_observations

        # Should we end the block?
        if total_delta + length_penalty >= cutoff:
            return True

        self.merge_new_observations()
        return False

    def reset(self) -> None:
        """Reset statistics when starting a new block."""
        self.observations = [0] * self.NUM_OBSERVATION_TYPES
        self.new_observations = [0] * self.NUM_OBSERVATION_TYPES
        self.num_observations = 0
        self.num_new_observations = 0
