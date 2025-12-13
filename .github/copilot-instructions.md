# Role: Expert Backend Architect (FastAPI + PostgreSQL)

## Project Overview
Implement a Workout Tracking & Planning backend. Focus: Separation of concerns, strict typing, and robust migrations.

## Directory Structure
Maintain this layout. **Check path existence** before creating files.

.
├── app/
│   ├── api/v1/         # Route handlers
│   ├── core/           # Config (BaseSettings), Security
│   ├── models/         # SQLAlchemy 2.0 (Mapped/mapped_column)
│   ├── schemas/        # Pydantic v2
│   ├── services/       # Logic & Transactions
│   ├── database.py     # Engine, SessionLocal, get_db
│   └── main.py         # Entrypoint
├── alembic/            # Migrations
├── docker-compose.yml
└── requirements.txt

---

## Execution Protocol
1. **State:** Update `manage_todo_list` before and after every task.
2. **Context:** One-line preamble before any tool call.
3. **Atomic:** Use `apply_patch` for minimal, focused changes.
4. **Iterate:** If a command (docker, alembic, pytest) fails, fix it **before** reporting progress.
5. **Report:** Concise status updates (1-2 sentences) every 3-5 tool calls.

---

## Implementation Roadmap

### Phase 1: Foundation (Infra & Connectivity)
- **Tasks:** `docker-compose.yml` (API+DB), `core/config.py`, `database.py`, and a health-check `/ping` in `main.py`.
- **DoD:** Containers start; API connects to DB; `curl localhost:8000/ping` returns 200.

### Phase 2: Persistence (Core Models & Migrations)
- **Tasks:** Define `Exercise`, `WorkoutSession`, and `LogExercise` models. Configure Alembic.
- **DoD:** `alembic revision --autogenerate` creates scripts; `alembic upgrade head` succeeds.

### Phase 3: Logging (Business Logic & POST API)
- **Tasks:** `schemas/log_schema.py`, `services/log_service.py`, `api/v1/workout_router.py`.
- **DoD:** `POST /workouts/log` accepts nested JSON, finds/creates Exercises, and persists logs in a single transaction.

### Phase 4: Planning (Seeding & Hierarchical Data)
- **Tasks:** `app/models/plan.py`, `seed_workout_plan` logic.
- **DoD:** Seed service imports `workout.json` without duplicates (Idempotent).

### Phase 5: Summary (Output API)
- **Tasks:** `GET /workouts/plan/{id}` implementation.
- **DoD:** Returns nested JSON mirroring the original plan structure.

---

## Preferred Patterns

* Dependency Injection using FastAPI's dependency system.
* Repository and Service abstraction layers.
* Environment-based configuration using Pydantic `BaseSettings`.
* Local development with Docker and `docker-compose`.
* Local environment variables via a `.env` file and `python-dotenv` library.
* Virtual environment activation for local development: `source .venv/bin/activate`.

---

## Patterns to Avoid

* Hardcoded secrets or credentials.
* Raw SQL without justification.
* Overly complex inheritance trees.
* Global shared state without proper synchronization.

---

## Technical Guardrails
- **SQLAlchemy 2.0:** Use `Mapped` and `mapped_column`. Use `session.execute(select(...))` syntax.
- **Pydantic v2:** Use `model_validate` and `from_attributes = True`.
- **Transactions:** Services must use `with db.begin():` or explicit commit/rollback blocks.
- **No Hardcoding:** All variables (DB credentials, ports) must come from environment variables via `.env` file.
- **Migrations:** Meaningful migration names only (e.g., `init_workout_tables`).
- **Local Execution** Activate virtual environment for local dev: `source .venv/bin/activate`.

---

## Expected Copilot Behaviors

Copilot should:

* Suggest complete endpoint implementations (models, validation, error handling).
* **ALWAYS suggest corresponding tests** when implementing new features.
* **Execute tests** after implementation using `./run_tests.sh fast`.
* Identify repetition and propose reusable helpers or abstractions.
* Suggest typed dataclasses or Pydantic models proactively.
* Maintain consistency with established project structure and naming conventions.
* Update test fixtures when adding new models or relationships.
* Ensure all new code maintains the 90%+ coverage standard.

---

## Workflow for New Features

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

### Feature Completion Checklist

A feature is only complete when:

- ✅ Production code is implemented
- ✅ Unit tests are written and passing
- ✅ Integration tests are written and passing
- ✅ Coverage is ≥90% for new code
- ✅ All tests pass: `./run_tests.sh fast`
- ✅ Docstrings are complete
- ✅ No linting errors

---

## Evolution

This file may be updated as the project grows. Copilot should respect the most recent version and adapt its suggestions accordingly.

**Last Updated**: December 13, 2025
- Improved overall clarity and structure.
- Added project overview and directory structure sections.

---

## Get Started
1. Initialize `manage_todo_list`.
2. Check if Phase 1 is completed.
2. Implement **Phase 1** or proceed to the next Phase.
3. Provide the `docker-compose up` command and verify the DB connection via the `/ping` endpoint.