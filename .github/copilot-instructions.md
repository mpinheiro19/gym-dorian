<!-- Copilot instructions for gym-dorian repository -->
# Guidance for AI coding agents
# copilot-instructions.md

This document defines formal guidelines for GitHub Copilot when assisting in Python backend engineering tasks within this repository. These instructions should be followed consistently to ensure code quality, maintainability, and alignment with project standards.

## 1. Purpose

GitHub Copilot must generate code and suggestions that adhere to the architectural, stylistic, and operational standards defined by this backend codebase. Copilot should prefer correctness, clarity, and long-term maintainability over brevity.

## 2. Coding Standards

* Follow **PEP 8**, type hinting, and idiomatic Python practices.
* Prefer clear, modular, and testable code structures.
* Avoid anti‑patterns, shortcuts, or insecure practices.
* Provide small contextual explanations only when beneficial.

## 3. Application Architecture

### 3.1 Framework

* Default framework: **FastAPI** (async-first design). Use async where appropriate.

### 3.2 Project Structure

Copilot should encourage and generate code following this structure:

```
app/
  api/
    routers/
    dependencies/
  core/
  models/
  services/
  repositories/
  db/
  tests/
```

### 3.3 API Design

* Use Pydantic models for request/response payloads.
* Provide clear routing, versioning, and error-handling patterns.
* Ensure proper separation between API layer, service layer, and data layer.

### 3.4 Database

* Use **SQLAlchemy 2.0** ORM patterns.
* Default database: **PostgreSQL**.
* Generate migration scaffolding using **Alembic** when applicable.

## 4. Testing Guidelines

### 4.1 Test-Driven Development

**CRITICAL**: When implementing new features, ALWAYS create tests alongside the code:

* **For new endpoints**: Create integration tests in `app/tests/integration/`
* **For new services**: Create unit tests with mocks in `app/tests/unit/`
* **For new models**: Add CRUD integration tests
* **Execute tests**: Run `./run_tests.sh fast` after implementation to validate

### 4.2 Testing Framework

* Use **pytest** as the primary testing framework.
* Prefer fixtures for database and environment setup.
* Maintain **minimum 90% code coverage** for new code.
* All tests must pass before considering a feature complete.

### 4.3 Test Structure

Follow the established test organization:

```
app/tests/
  ├── unit/              # Unit tests (mocked dependencies)
  ├── integration/       # API/Database tests
  └── fixtures/          # Test data factories
```

### 4.4 Test Patterns

* **Use AAA pattern**: Arrange, Act, Assert
* **Descriptive names**: `test_create_exercise_with_valid_data_returns_201`
* **Use factories**: Leverage `ExerciseFactory`, `WorkoutSessionFactory`, etc.
* **Isolated tests**: Each test must run independently
* **Fast tests**: Keep tests fast (prefer SQLite in-memory for unit/integration tests)

### 4.5 Test Examples

**Integration test for new endpoint:**
```python
@pytest.mark.integration
class TestMyEndpoint:
    def test_create_resource(self, client: TestClient):
        response = client.post("/api/v1/resource", json={"name": "Test"})
        assert response.status_code == 201
        assert response.json()["name"] == "Test"
```

**Unit test for service:**
```python
@pytest.mark.unit
class TestMyService:
    def test_calculation(self):
        mock_db = Mock()
        result = my_service.calculate(mock_db, 10, 20)
        assert result == 30
```

### 4.6 Running Tests

After implementing features, ALWAYS run:

```bash
# Quick validation during development
./run_tests.sh fast

# Full test suite with coverage before commit
./run_tests.sh coverage

# Specific test file
pytest app/tests/integration/test_my_feature.py -v
```

## 5. Documentation Standards

* Produce Google-style or NumPy-style docstrings for functions, classes, and modules.
* Include inline comments only when the logic is non-obvious.
* Prefer clarity over verbosity.

## 6. DevOps & Tooling

* Dockerfiles should follow best-practice multi-stage builds.
* Use `black`, `isort`, `flake8`, and `mypy` for formatting/linting.
* CI suggestions should default to GitHub Actions.

## 7. Preferred Patterns

* Dependency Injection using FastAPI's dependency system.
* Repository and Service abstraction layers.
* Environment-based configuration using Pydantic `BaseSettings`.

## 8. Patterns to Avoid

* Hardcoded secrets or credentials.
* Raw SQL without justification.
* Overly complex inheritance trees.
* Global shared state without proper synchronization.

## 9. Expected Copilot Behaviors

Copilot should:

* Suggest complete endpoint implementations (models, validation, error handling).
* **ALWAYS suggest corresponding tests** when implementing new features.
* **Execute tests** after implementation using `./run_tests.sh fast`.
* Identify repetition and propose reusable helpers or abstractions.
* Suggest typed dataclasses or Pydantic models proactively.
* Maintain consistency with established project structure and naming conventions.
* Update test fixtures when adding new models or relationships.
* Ensure all new code maintains the 90%+ coverage standard.

## 10. Workflow for New Features

When implementing a new feature, follow this sequence:

1. **Understand requirements** - Clarify the feature specification
2. **Design the solution** - Plan models, services, endpoints
3. **Implement the code** - Write production code following standards
4. **Write tests simultaneously** - Create unit and integration tests
5. **Execute tests** - Run `./run_tests.sh fast` to validate
6. **Check coverage** - Ensure new code meets 90%+ coverage
7. **Fix issues** - Address any failing tests or coverage gaps
8. **Document** - Update docstrings and relevant documentation
9. **Final validation** - Run full test suite before considering complete

### 10.1 Feature Completion Checklist

A feature is only complete when:

- ✅ Production code is implemented
- ✅ Unit tests are written and passing
- ✅ Integration tests are written and passing
- ✅ Coverage is ≥90% for new code
- ✅ All tests pass: `./run_tests.sh fast`
- ✅ Docstrings are complete
- ✅ No linting errors

## 11. Evolution

This file may be updated as the project grows. Copilot should respect the most recent version and adapt its suggestions accordingly.

**Last Updated**: December 11, 2025 - Added comprehensive testing guidelines and workflow
