# 🧪 Quick Start - Test Suite

## ⚡ Run Tests

```bash
# Run all tests (fastest)
pytest

# Run with script convenience
./run_tests.sh all

# Run only fast tests
./run_tests.sh fast

# Run with coverage
./run_tests.sh coverage
```

## 📁 Test Files

```
app/tests/
├── unit/
│   ├── test_factories.py       (12 tests)
│   └── test_services.py        (12 tests)
└── integration/
    ├── test_health.py          (9 tests)
    ├── test_exercise_model.py  (10 tests)
    ├── test_workout_models.py  (18 tests)
    └── test_performance.py     (10 tests)
```

## 🎯 Common Commands

```bash
# Unit tests only
pytest -m unit

# Integration tests only  
pytest -m integration

# Specific file
pytest app/tests/integration/test_health.py -v

# Coverage report
pytest --cov=app --cov-report=html
open htmlcov/index.html  # View in browser
```

## 🚀 Next Steps

When adding new features:

1. **Add endpoint** → Add integration test
2. **Add service** → Add unit test with mocks
3. **Add model** → Add CRUD integration tests
4. Run tests before committing: `./run_tests.sh fast`

---

Happy Testing! 🧪✨
