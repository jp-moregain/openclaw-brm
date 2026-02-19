# Contributing to OpenClaw Agent BRM

First off, thank you for considering contributing to OpenClaw Agent BRM! It's people like you that make this tool better for the OpenClaw community.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues to see if the problem has already been reported. When you are creating a bug report, please include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples to demonstrate the steps**
- **Describe the behavior you observed and what behavior you expected**
- **Include code samples and command outputs**

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

- **Use a clear and descriptive title**
- **Provide a step-by-step description of the suggested enhancement**
- **Provide specific examples to demonstrate the enhancement**
- **Explain why this enhancement would be useful**

### Pull Requests

1. Fork the repository
2. Create a new branch from `main` for your feature or bug fix
3. Make your changes
4. Add or update tests as necessary
5. Update documentation if needed
6. Submit a pull request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/openclaw-brm.git
cd openclaw-brm

# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Run tests
python -m pytest tests/
```

## Style Guidelines

### Python Code

- Follow PEP 8 style guide
- Use type hints where appropriate
- Add docstrings to functions and classes
- Keep functions focused and small

### Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

Example:
```
Add dry-run mode to backup command

- Preview what would be backed up without creating files
- Useful for testing and validation
- Closes #123
```

## Testing

- Write tests for new functionality
- Ensure all tests pass before submitting PR
- Test with real OpenClaw agents when possible

## Documentation

- Update README.md if adding new features
- Update CHANGELOG.md with your changes
- Add examples for complex features

## Questions?

Feel free to open an issue with your question or join our discussions!

Thank you for contributing! 🎉
