# AGENT INSTRUCTIONS for /tests

## Scope
These rules cover the test suite under `tests/`.

## Test Guidelines
- Tests use **pytest** exclusively. Each file should start with standard imports
  followed by fixtures and test cases.
- Name test files starting with `test_` and use descriptive function names.
- Keep tests isolated; avoid network calls or external services.
- Temporary files should use Python's `tmp_path` fixture.

## Running Tests
Execute all tests from the repository root with:
```bash
PYTHONPATH="$PWD" pytest
```
All tests should pass before committing. If failures are expected, document the
reason in the commit message.
