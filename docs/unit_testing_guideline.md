# Pytest Unit Testing Guidelines

- All Python source code is located in the @src directory.
- All tests are located in the @tests directory.
- To run tests, ensure the `src` directory is added to the `PYTHONPATH` so modules can be imported correctly.
- Use `pytest` as the test runner. Example command:
  ```sh
  PYTHONPATH=src pytest tests/
  ```
- Test files should be named `test_*.py` or `*_test.py` and placed in the `tests` directory or its subdirectories.
- Each test function should start with `test_` and use standard `pytest` assertions.
- For fixtures, use `conftest.py` in the `tests` directory as needed.
- For more details, see the @pytest documentation.

## 1. Test Structure & Organization

- Place all tests in the `tests/` directory,
- Name test files as `test_*.py`.
- Each test module should test a single module or feature.
- Group related tests into classes prefixed with `Test` (no `__init__` method).

## 2. Test Naming & Clarity

- Test function names must be descriptive: `test_<functionality>_<expected_behavior>`.
- Use docstrings to clarify intent, especially for edge cases or complex scenarios.
- Avoid abbreviations in test names.

## 3. Test Coverage & TDD Discipline

- 100% code coverage is required for all public code.
- Every feature/bugfix must start with a failing test (TDD loop).
- Each test suite must include:
  - At least one happy-path test
  - At least one edge case test
  - At least one error-handling or security test
- Use `PYTHONPATH=src pytest --cov=src` to check coverage before every commit.

## 4. Test Independence & Isolation

- Tests must not depend on each other or external state.
- Use fixtures for setup/teardown; prefer `@pytest.fixture` over `setUp`/`tearDown`.
- Avoid global state or side effects.

## 5. Assertions & Error Handling

- Use plain `assert` statements for clarity.
- For exceptions, use `pytest.raises` context manager.
- Always assert on both output and side effects.

## 6. Parametrization & DRY Principle

- Use `@pytest.mark.parametrize` to test multiple inputs/outputs efficiently.
- Extract common setup logic into fixtures.
- Avoid duplicating test logic.

## 7. Mocking & Fakes

- Use `unittest.mock` or `pytest-mock` for mocking dependencies.
- Only mock external systems or slow operations (e.g., randomness, I/O).
- Prefer real objects for simple, fast dependencies.

## 8. Linting & Formatting

- Test code must follow the same PEP8/PEP257 standards as production code.
- Use `flake8` to lint test files. Install with `pip install flake8`.
- Use `black` to format test files. Install with `pip install black`.

## 9. Running Tests

- Run all tests with `pytest` from the project root.
- Use `pytest -v` for verbose output during development.
- Run the full suite before every commit and PR.

## 10. Documentation & Review

- Document non-obvious test logic with comments or docstrings.
- All new/changed tests must be reviewed in PRs.
- Update tests when refactoring or changing public APIs.
