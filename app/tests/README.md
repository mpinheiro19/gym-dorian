# Test Suite Documentation

## Overview

This test suite provides comprehensive testing for the Gym Dorian API, including unit tests, integration tests, and end-to-end tests.

## Structure

```
tests/
├── __init__.py              # Test package initialization
├── conftest.py              # Shared fixtures and pytest configuration
├── unit/                    # Unit tests for services and business logic
│   ├── __init__.py
│   └── test_factories.py    # Tests for factory functions
├── integration/             # Integration tests for API endpoints and database
│   ├── __init__.py
│   ├── test_health.py       # Health check and API configuration tests
│   ├── test_exercise_model.py    # Exercise model CRUD tests
│   └── test_workout_models.py    # Workout and log model tests
└── fixtures/                # Test data factories and helpers
    ├── __init__.py
    └── factories.py         # Factory functions for test data
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run with verbose output
```bash
pytest -v
```

### Run specific test categories
```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only fast tests (exclude slow tests)
pytest -m "not slow"
```

### Run specific test files
```bash
# Run health check tests
pytest app/tests/integration/test_health.py

# Run exercise model tests
pytest app/tests/integration/test_exercise_model.py
```

### Run specific test classes or functions
```bash
# Run a specific test class
pytest app/tests/integration/test_health.py::TestHealthEndpoint

# Run a specific test function
pytest app/tests/integration/test_health.py::TestHealthEndpoint::test_root_endpoint_returns_200
```

### Coverage Reports
```bash
# Generate HTML coverage report
pytest --cov=app --cov-report=html

# View coverage in terminal
pytest --cov=app --cov-report=term-missing

# Generate XML coverage for CI/CD
pytest --cov=app --cov-report=xml
```

## Test Fixtures

### Database Fixtures

- **`db_session`**: Provides a clean database session for each test
- **`client`**: Provides a TestClient with database dependency overrides

### Data Fixtures

- **`sample_exercises`**: Creates 4 sample exercises for testing
- **`sample_workout_session`**: Creates a workout session with logged exercises

### Factory Functions

Use factory functions from `tests.fixtures.factories` to create test data:

```python
from app.tests.fixtures.factories import ExerciseFactory, WorkoutSessionFactory

# Create a single exercise
exercise = ExerciseFactory.create(name="Bench Press", muscle_group="Chest")

# Create multiple exercises
exercises = ExerciseFactory.create_batch(5)

# Create a workout session
session = WorkoutSessionFactory.create(duration_minutes=45)
```

## Writing New Tests

### Unit Tests

Place unit tests in `tests/unit/`. Unit tests should:
- Test individual functions or classes in isolation
- Mock external dependencies
- Be fast and deterministic
- Use the `@pytest.mark.unit` marker (automatically applied)

Example:
```python
import pytest

@pytest.mark.unit
class TestMyService:
    def test_calculation(self):
        result = my_service.calculate(5, 10)
        assert result == 15
```

### Integration Tests

Place integration tests in `tests/integration/`. Integration tests should:
- Test API endpoints and database interactions
- Use the `client` and `db_session` fixtures
- Test realistic scenarios
- Use the `@pytest.mark.integration` marker (automatically applied)

Example:
```python
import pytest
from fastapi.testclient import TestClient

@pytest.mark.integration
class TestExerciseEndpoints:
    def test_create_exercise(self, client: TestClient):
        response = client.post("/api/v1/exercises", json={
            "name": "Squat",
            "muscle_group": "Legs"
        })
        assert response.status_code == 201
```

## Best Practices

1. **Descriptive Test Names**: Use clear, descriptive test function names
   - Good: `test_create_exercise_with_valid_data_returns_201`
   - Bad: `test_1`, `test_exercise`

2. **Arrange-Act-Assert Pattern**: Structure tests clearly
   ```python
   def test_example(self, db_session):
       # Arrange
       exercise = Exercise(name="Test")
       
       # Act
       db_session.add(exercise)
       db_session.commit()
       
       # Assert
       assert exercise.id is not None
   ```

3. **Use Fixtures**: Leverage pytest fixtures for setup and teardown
4. **Test Edge Cases**: Include tests for error conditions and edge cases
5. **Keep Tests Independent**: Each test should be able to run in isolation
6. **Use Factories**: Use factory functions for creating test data
7. **Document Complex Tests**: Add docstrings to explain what complex tests verify

## Continuous Integration

The test suite is designed to work with CI/CD pipelines. The following commands are recommended:

```bash
# Fast smoke tests for quick feedback
pytest -m "not slow" --tb=short

# Full test suite with coverage
pytest --cov=app --cov-report=xml --cov-report=term

# Generate coverage badge
coverage-badge -o coverage.svg -f
```

## Troubleshooting

### Tests are slow
- Use `pytest -m "not slow"` to run only fast tests
- Check for unnecessary database operations
- Consider using mocks for external dependencies

### Database errors
- Ensure all fixtures are properly cleaning up
- Check that `db_session` fixture is being used
- Verify SQLite compatibility for your queries

### Import errors
- Ensure you're running tests from the project root
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check PYTHONPATH configuration

## Metrics and Coverage Goals

- **Minimum Coverage**: 80%
- **Target Coverage**: 90%+
- **Critical Paths**: 100% (authentication, data integrity)

Run `pytest --cov=app --cov-report=term-missing` to see which lines are not covered.
