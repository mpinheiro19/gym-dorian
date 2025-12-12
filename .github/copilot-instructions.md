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

* Use **pytest** as the primary testing framework.
* Prefer fixtures for database and environment setup.
* Encourage high coverage and meaningful tests.

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
* Identify repetition and propose reusable helpers or abstractions.
* Suggest typed dataclasses or Pydantic models proactively.
* Maintain consistency with established project structure and naming conventions.

## 10. Evolution

This file may be updated as the project grows. Copilot should respect the most recent version and adapt its suggestions accordingly.
