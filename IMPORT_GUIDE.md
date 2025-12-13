# Import Structure Guide

## 📁 Project Structure

This project uses a consistent import structure across both local development and Docker environments.

```
/home/user/Codes/gym-dorian/          (Local root)
├── app/                               (Application code - mapped to /app in Docker)
│   ├── main.py
│   ├── database.py
│   ├── core/
│   │   └── config.py
│   ├── models/
│   │   ├── base.py
│   │   ├── exercise.py
│   │   └── log.py
│   ├── api/
│   ├── services/
│   ├── schemas/
│   └── tests/
├── alembic/
├── docker-compose.yml
├── Dockerfile
└── pytest.ini
```

## 🎯 Import Strategy

### Relative Imports (Always Use This)

All Python files should use **relative imports** from the `app/` directory as root:

```python
# ✅ CORRECT - Works in both local and Docker
from database import get_db
from models.base import Base
from models.exercise import Exercise
from core.config import settings
from services.plan_service import PlanService
```

```python
# ❌ WRONG - Don't use absolute imports with 'app.' prefix
from app.database import get_db        # ❌ Wrong
from app.models.base import Base       # ❌ Wrong
from app.core.config import settings   # ❌ Wrong
```

### Why This Works

**Local Development:**
- `pytest.ini` sets `pythonpath = app`
- Makes pytest run as if you're inside the `app/` directory
- Imports resolve from `app/` as root

**Docker Container:**
- `Dockerfile` sets `WORKDIR /app`
- `docker-compose.yml` maps `./app:/app`
- Code runs from `/app` directory
- Imports resolve from `/app` as root

## 🔧 Configuration Files

### pytest.ini
```ini
[tool:pytest]
pythonpath = app          # ← Makes local tests work like Docker
testpaths = app/tests
```

### Dockerfile
```dockerfile
WORKDIR /app              # ← Sets working directory
COPY app/ .               # ← Copies app/* to /app/
```

### docker-compose.yml
```yaml
volumes:
  - ./app:/app            # ← Maps local app/ to container /app/
```

## ✅ Consistency Benefits

1. **Same imports everywhere**: Application code, tests, and scripts use identical imports
2. **No sys.path hacks**: No need for `sys.path.insert()` in test files
3. **Docker parity**: Local environment behaves exactly like Docker
4. **IDE support**: Better autocomplete and type checking
5. **Maintainability**: New developers see consistent patterns

## 🧪 Testing

Both commands work identically:

```bash
# Local testing
pytest

# Docker testing (if needed)
docker exec gym_tracker_api pytest
```

## 📝 Examples

### Application Code
```python
# app/main.py
from fastapi import FastAPI
from database import engine, Base
from api.v1 import workout_router
from models import exercise, log
```

### Test Files
```python
# app/tests/integration/test_database.py
import pytest
from models.base import Base
from database import get_db
from sqlalchemy import create_engine
```

### Service Layer
```python
# app/services/plan_service.py
from sqlalchemy.orm import Session
from models.plan import Plan
from schemas.plan_schema import PlanCreate
from core.config import settings
```

## 🚀 Running the Application

**Local Development:**
```bash
cd app
uvicorn main:app --reload
```

**Docker:**
```bash
docker-compose up
# Runs: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Both use the same import structure!

## ⚠️ Common Mistakes

1. **Don't add `app.` prefix to imports:**
   ```python
   from app.models.base import Base  # ❌ Wrong
   from models.base import Base      # ✅ Correct
   ```

2. **Don't use sys.path manipulation:**
   ```python
   import sys
   sys.path.insert(0, '../..')  # ❌ Not needed anymore
   ```

3. **Don't import from parent directory:**
   ```python
   from ..app.models import Base  # ❌ Wrong
   from models.base import Base   # ✅ Correct
   ```

## 🎓 Best Practices

1. **Always import from root**: Treat `app/` as your import root
2. **Use explicit imports**: Import specific classes/functions, not modules
3. **Keep consistency**: Same pattern in all files (main, tests, services)
4. **Trust pytest.ini**: Let pytest configuration handle the path setup

---

**Last Updated**: December 11, 2025  
**Applies to**: All Python code in `app/` directory
