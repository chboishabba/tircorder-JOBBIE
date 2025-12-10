# AGENTS

## Code Style
- Follow PEP 8 with Black formatting (line length 88).
- Use 4-space indentation and include docstrings for public functions.

## Testing
Run tests before committing:

```
PYENV_VERSION=3.10.17 PYTHONPATH=. pytest tests/test_calendar_utils.py -q
```

## Pull Requests
Include a summary of changes and the test command output in PR descriptions.
