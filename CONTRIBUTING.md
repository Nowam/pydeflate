# Contributing to pydeflate

Thank you for your interest in contributing to the pydeflate project! We welcome contributions of all kinds, from bug reports to feature implementations.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Development Setup

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/Nowam/pydeflate.git
   cd pydeflate
   ```

2. Set up your development environment:
   ```bash
   uv sync --dev
   ```

3. Verify the setup by running tests:
   ```bash
   uv run pytest tests/
   ```

## Code Style and Standards

We use [Ruff](https://docs.astral.sh/ruff/) for code formatting and linting:

```bash
# Check formatting and linting
uv run ruff check .
uv run ruff format .

# Auto-fix issues where possible
uv run ruff check --fix .
```

### Code Guidelines

- Follow PEP 8 style guidelines (enforced by Ruff)
- Use type hints for all function parameters and return values
- Write clear, descriptive docstrings for all public functions and classes
- Keep functions focused and single-purpose
- Add tests for new functionality

## Testing

### Running Tests

```bash
# Run all tests
uv run pytest tests/

# Run tests with verbose output
uv run pytest tests/ -v

# Test specific functionality
uv run python main.py test samples/Samp1.bin
```

### Writing Tests

- Add tests for any new functionality in the `tests/` directory
- Use descriptive test function names that explain what is being tested
- Include both positive and negative test cases
- Test edge cases and error conditions

## Submitting Changes

### Pull Request Process

1. Create a new branch for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and ensure all tests pass:
   ```bash
   uv run pytest tests/
   uv run ruff check .
   ```

3. Commit your changes with clear, descriptive messages:
   ```bash
   git add .
   git commit -m "Add feature: brief description of changes"
   ```

4. Push your branch and create a pull request:
   ```bash
   git push origin feature/your-feature-name
   ```

### Pull Request Guidelines

- Provide a clear description of the changes and their purpose
- Reference any related issues using `#issue-number`
- Include test cases for new functionality
- Ensure all CI checks pass
- Update documentation if necessary

## Types of Contributions

### Bug Reports

When reporting bugs, please include:
- Clear description of the issue
- Steps to reproduce the problem
- Expected vs. actual behavior
- Python version and operating system
- Sample files that demonstrate the issue (if applicable)

### Feature Requests

For new features:
- Describe the use case and benefits
- Provide examples of how the feature would be used
- Consider the impact on existing functionality
- Be open to discussion about implementation approaches

### Code Contributions

We welcome contributions in these areas:
- Performance optimizations
- Algorithm improvements
- Additional compression formats
- Better error handling
- Documentation improvements
- Test coverage enhancements

## Algorithm Implementation Guidelines

When contributing to the compression algorithms:

- Maintain compatibility with the DEFLATE specification (RFC 1951)
- Preserve data integrity - all changes must pass round-trip tests
- Document any algorithmic choices or optimizations
- Consider both compression ratio and speed trade-offs
- Add benchmarks for performance-related changes

## Development Tips

### Understanding the Codebase

- `compressors/deflate.py`: Main DEFLATE implementation
- `compressors/lz77.py`: LZ77 compression algorithm
- `compressors/huffman.py`: Huffman coding implementation
- `compressors/helpers/`: Utility functions and helpers
- `main.py`: CLI interface
- `tests/`: Test suite

### Debugging

Use the round-trip test functionality to verify correctness:
```bash
python main.py test your-test-file.txt
```

For performance testing:
```bash
python main.py compress large-file.txt
```

## Questions and Support

If you have questions or need help:
- Check existing issues and discussions
- Create a new issue with the "question" label
- Be specific about what you're trying to achieve

## Code of Conduct

Please be respectful and constructive in all interactions. We're committed to providing a welcoming environment for all contributors.

Thank you for contributing to pydeflate!