# Gym Dorian — Backend API

A comprehensive fitness tracking and analytics API built with FastAPI, designed to help users log workouts, track progress, and analyze fitness data over time.

This project is designed as a hands-on exploration of modern AI-assisted development, serving as a sandbox to **evaluate** and **master** tools such as **GitHub Copilot**, **Claude Code**, and other emerging LLM-based workflows. The codebase and architecture are **intentionally** shaped to <ins>test the limits of AI pair-programming, automated refactoring, and agentic coding patterns</ins>.

## Quick Summary

- **API Framework**: FastAPI
- **ORM**: SQLAlchemy
- **Migrations**: Alembic
- **Database**: PostgreSQL (via Docker)
- **Authentication**: JWT (JSON Web Tokens)
- **Documentation**: Auto-generated with Swagger UI at `/docs`

## Table of Contents

- [Features](#features)
- [Installation & Setup](#installation--setup)
- [Project Structure](#project-structure)
- [Getting Started Guide](#getting-started-guide)
- [API Documentation](#api-documentation)
- [Database Migrations](#database-migrations)
- [Configuration](#configuration)
- [To Be Done](#to-be-done)

## Features

- **User Authentication**: Secure registration, login, and JWT-based authentication
- **User Management**: Profile management, settings, and fitness goals
- **Exercise Library**: Create and manage custom exercises with muscle groups and equipment types
- **Workout Logging**: Log workout sessions with detailed set-by-set tracking (reps, weight, RPE)
- **Analytics Dashboard**: Track progress over time with analytical views and statistics
- **Admin Tools**: User management and system administration endpoints
- **Set-Level Tracking**: Track individual sets with detailed metrics (reps, weight, RPE, notes)
- **Muscle Group Tracking**: Track agonist and synergist muscle groups for exercises

## Installation & Setup

### Requirements

- Docker & Docker Compose (recommended)
- Python 3.11+ (for local development without Docker)
- PostgreSQL (if running without Docker)

### Running with Docker (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd gym-dorian
```

2. Copy the example environment file and configure it:
```bash
cp .env.example .env
# Edit .env with your settings (optional, defaults work for development)
```

3. Start the services:
```bash
docker-compose up --build -d
```

4. Check API logs:
```bash
docker logs -f gym_tracker_api
```

5. Access the API:
   - API Health Check: `http://localhost:8000/`
   - Interactive Documentation: `http://localhost:8000/docs`
   - Alternative Docs: `http://localhost:8000/redoc`

### Running Locally (Without Docker)

1. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your PostgreSQL connection details
```

4. Run database migrations:
```bash
alembic upgrade head
```

5. Start the API server:
```bash
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

6. Access the API at `http://localhost:8000/docs`

## Configuration

The application uses Pydantic Settings for configuration management through environment variables.

### Environment Variables

Create a `.env` file in the root directory (copy from `.env.example`):

```env
# Database Configuration (Required)
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/gym_dorian

# Security (Required for production)
SECRET_KEY=your-secret-key-here-generate-with-openssl-rand-hex-32
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Environment State (Optional, default: development)
ENV_STATE=development  # Options: development, staging, production
```

### Configuration Priority

1. System environment variables (highest priority)
2. `.env` file in project root
3. Default values in code (lowest priority)

### Generating a Secret Key

```bash
openssl rand -hex 32
```

## Project Structure

```
gym-dorian/
├── app/                          # Main application code
│   ├── api/                      # API routes and endpoints
│   │   ├── dependencies/         # Dependency injection (auth, etc.)
│   │   ├── routes/               # Route handlers
│   │   │   ├── auth.py          # Authentication endpoints
│   │   │   ├── users.py         # User profile & settings
│   │   │   ├── workouts.py      # Workout logging
│   │   │   ├── analytics.py    # Progress tracking & stats
│   │   │   └── admin.py         # Admin endpoints
│   │   └── v1/                  # API versioning
│   ├── core/                    # Core functionality
│   │   ├── config.py            # Configuration management
│   │   └── security.py          # Password hashing, JWT tokens
│   ├── crud/                    # Database CRUD operations
│   │   ├── user.py              # User operations
│   │   ├── workout.py           # Workout operations
│   │   ├── analytics.py         # Analytics queries
│   │   └── admin.py             # Admin operations
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── user.py              # User, UserSettings, UserGoal
│   │   ├── exercise.py          # Exercise model
│   │   ├── log.py               # WorkoutSession, LogExercise, SetDetail
│   │   ├── plan.py              # Workout plans (future)
│   │   ├── enums.py             # Enum types
│   │   └── base.py              # Base model class
│   ├── schemas/                 # Pydantic schemas (validation)
│   │   ├── user_schema.py       # User DTOs
│   │   ├── workout_schema.py    # Workout DTOs
│   │   ├── log_schema.py        # Exercise log DTOs
│   │   ├── analytics_schema.py  # Analytics DTOs
│   │   └── admin_schema.py      # Admin DTOs
│   ├── services/                # Business logic layer
│   │   ├── log_service.py       # Workout logging logic
│   │   └── plan_service.py      # Workout plans (future)
│   ├── main.py                  # FastAPI application entry point
│   └── database.py              # Database connection & session
├── alembic/                     # Database migrations
│   ├── versions/                # Migration scripts
│   └── env.py                   # Alembic configuration
├── tests/                       # Test suite
│   ├── test_auth.py            # Authentication tests
│   ├── test_workouts.py        # Workout tests
│   └── test_analytics.py       # Analytics tests
├── postman/                     # Postman collections
├── alembic.ini                  # Alembic configuration file
├── docker-compose.yml           # Docker services configuration
├── Dockerfile                   # API container definition
├── requirements.txt             # Python dependencies
├── .env.example                 # Example environment variables
├── AUTH_API_GUIDE.md           # Authentication API documentation
├── WORKOUT_API_GUIDE.md        # Workout API documentation
├── ANALYTICS_API_GUIDE.md      # Analytics API documentation
└── ADMIN_API_GUIDE.md          # Admin API documentation
```

## Getting Started Guide

This section provides a step-by-step guide for new users to start using the Gym Dorian API.

### Step 1: Create an Account

Register a new user account using the `/api/auth/register` endpoint.

**Using cURL:**
```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "password": "securePassword123",
    "full_name": "John Doe"
  }'
```

**Response:**
```json
{
  "id": 1,
  "email": "john.doe@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-12-20T10:00:00Z",
  "last_login": null
}
```

### Step 2: Login and Get Access Token

Login to receive a JWT token for authenticated requests.

**Using cURL:**
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john.doe@example.com&password=securePassword123"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Save this token!** You'll need it for all subsequent requests.

**Pro Tip:** Store the token in an environment variable:
```bash
export TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Step 3: Create Exercises

Before logging workouts, create exercises in your library.

**Create Bench Press Exercise:**
```bash
curl -X POST "http://localhost:8000/api/workouts/exercises" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Bench Press",
    "muscle_group": "Chest",
    "equipment_type": "Barbell",
    "agonist_muscle_groups": ["Chest"],
    "synergist_muscle_groups": ["Shoulders", "Triceps"]
  }'
```

**Response:**
```json
{
  "id": 1,
  "name": "Bench Press",
  "muscle_group": "Chest",
  "equipment_type": "Barbell",
  "agonist_muscle_groups": ["Chest"],
  "synergist_muscle_groups": ["Shoulders", "Triceps"]
}
```

**Create Multiple Exercises:**
```bash
# Squat
curl -X POST "http://localhost:8000/api/workouts/exercises" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Squat",
    "muscle_group": "Legs",
    "equipment_type": "Barbell",
    "agonist_muscle_groups": ["Quadriceps", "Glutes"],
    "synergist_muscle_groups": ["Hamstrings", "Calves"]
  }'

# Deadlift
curl -X POST "http://localhost:8000/api/workouts/exercises" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Deadlift",
    "muscle_group": "Back",
    "equipment_type": "Barbell",
    "agonist_muscle_groups": ["Lower Back", "Glutes"],
    "synergist_muscle_groups": ["Hamstrings", "Traps"]
  }'
```

**View All Your Exercises:**
```bash
curl -X GET "http://localhost:8000/api/workouts/exercises" \
  -H "Authorization: Bearer $TOKEN"
```

### Step 4: Log Your First Workout

There are two methods to log workouts: **Standard Logging** and **Quick Logging** (recommended).

#### Method A: Quick Logging (Recommended)

This method allows you to log individual sets with detailed tracking.

```bash
curl -X POST "http://localhost:8000/api/workouts/sessions/quick" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "workout_date": "2025-12-20",
    "duration_minutes": 75,
    "notes": "Great chest day!",
    "exercises": [
      {
        "exercise_id": 1,
        "sets": [
          {"set_number": 1, "reps": 10, "weight": 60.0, "rpe": 7},
          {"set_number": 2, "reps": 10, "weight": 70.0, "rpe": 8},
          {"set_number": 3, "reps": 8, "weight": 80.0, "rpe": 9},
          {"set_number": 4, "reps": 6, "weight": 85.0, "rpe": 10}
        ]
      }
    ]
  }'
```

The API automatically calculates:
- `sets_completed`: 4 (count of sets)
- `top_weight`: 85.0 (maximum weight)
- `total_reps`: 34 (sum of all reps)

#### Method B: Standard Logging

Provide aggregated data if you don't need set-by-set tracking.

```bash
curl -X POST "http://localhost:8000/api/workouts/sessions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "workout_date": "2025-12-20",
    "duration_minutes": 75,
    "notes": "Great workout!",
    "exercises": [
      {
        "exercise_id": 1,
        "sets_completed": 4,
        "top_weight": 85.0,
        "total_reps": 34
      }
    ]
  }'
```

### Step 5: View Your Workout History

**Get All Workouts:**
```bash
curl -X GET "http://localhost:8000/api/workouts/sessions" \
  -H "Authorization: Bearer $TOKEN"
```

**Get Workouts in a Date Range:**
```bash
curl -X GET "http://localhost:8000/api/workouts/sessions?start_date=2025-12-01&end_date=2025-12-31" \
  -H "Authorization: Bearer $TOKEN"
```

**Get a Specific Workout:**
```bash
curl -X GET "http://localhost:8000/api/workouts/sessions/1" \
  -H "Authorization: Bearer $TOKEN"
```

### Step 6: Using CRUD Operations

#### Update a Workout Session

Modify workout details like duration or notes:

```bash
curl -X PUT "http://localhost:8000/api/workouts/sessions/1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "duration_minutes": 90,
    "notes": "Updated: Felt stronger today!"
  }'
```

#### Add an Exercise to an Existing Workout

```bash
curl -X POST "http://localhost:8000/api/workouts/sessions/1/exercises" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "exercise_id": 2,
    "sets_completed": 3,
    "top_weight": 100.0,
    "total_reps": 15
  }'
```

#### Update a Logged Exercise

Modify an exercise within a workout:

```bash
curl -X PUT "http://localhost:8000/api/workouts/exercises/logged/1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "top_weight": 90.0,
    "total_reps": 36
  }'
```

#### Delete a Logged Exercise

Remove an exercise from a workout:

```bash
curl -X DELETE "http://localhost:8000/api/workouts/exercises/logged/1" \
  -H "Authorization: Bearer $TOKEN"
```

#### Delete a Workout Session

```bash
curl -X DELETE "http://localhost:8000/api/workouts/sessions/1" \
  -H "Authorization: Bearer $TOKEN"
```

### Step 7: Update User Settings

Customize your preferences:

```bash
curl -X PUT "http://localhost:8000/api/users/me/settings" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "weight_unit": "kg",
    "distance_unit": "km",
    "default_rest_time": 90,
    "private_profile": false,
    "email_notifications": true
  }'
```

### Step 8: Set Fitness Goals

Create a fitness goal to track:

```bash
curl -X POST "http://localhost:8000/api/users/me/goals" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "goal_type": "strength",
    "title": "Bench Press 100kg",
    "description": "Reach 100kg bench press by end of year",
    "target_value": 100.0,
    "current_value": 85.0,
    "target_date": "2025-12-31"
  }'
```

### Using Python Instead of cURL

Here's a complete Python example:

```python
import requests
from datetime import date

BASE_URL = "http://localhost:8000/api"

# 1. Register
response = requests.post(
    f"{BASE_URL}/auth/register",
    json={
        "email": "jane@example.com",
        "password": "securePass123",
        "full_name": "Jane Smith"
    }
)
print("Registration:", response.json())

# 2. Login
response = requests.post(
    f"{BASE_URL}/auth/login",
    data={
        "username": "jane@example.com",
        "password": "securePass123"
    }
)
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 3. Create Exercise
response = requests.post(
    f"{BASE_URL}/workouts/exercises",
    headers=headers,
    json={
        "name": "Bench Press",
        "muscle_group": "Chest",
        "equipment_type": "Barbell"
    }
)
exercise = response.json()
print("Exercise Created:", exercise)

# 4. Log Workout
response = requests.post(
    f"{BASE_URL}/workouts/sessions/quick",
    headers=headers,
    json={
        "workout_date": str(date.today()),
        "duration_minutes": 60,
        "exercises": [
            {
                "exercise_id": exercise["id"],
                "sets": [
                    {"set_number": 1, "reps": 10, "weight": 60.0, "rpe": 7},
                    {"set_number": 2, "reps": 10, "weight": 70.0, "rpe": 8},
                    {"set_number": 3, "reps": 8, "weight": 80.0, "rpe": 9}
                ]
            }
        ]
    }
)
workout = response.json()
print("Workout Logged:", workout)

# 5. Get Workout History
response = requests.get(f"{BASE_URL}/workouts/sessions", headers=headers)
print("Workout History:", response.json())
```

## API Documentation

Once the API is running, you can access comprehensive interactive documentation:

### Swagger UI (Recommended)
Visit `http://localhost:8000/docs` for an interactive API explorer where you can:
- Browse all available endpoints
- View request/response schemas
- Test endpoints directly in the browser
- See authentication requirements

### ReDoc
Visit `http://localhost:8000/redoc` for a clean, readable API reference.

### Detailed Guides

For more detailed information about specific API features, see:

- **[AUTH_API_GUIDE.md](./AUTH_API_GUIDE.md)** - Complete authentication and user management guide
- **[WORKOUT_API_GUIDE.md](./WORKOUT_API_GUIDE.md)** - Workout logging and exercise management
- **[ANALYTICS_API_GUIDE.md](./ANALYTICS_API_GUIDE.md)** - Progress tracking and statistics
- **[ADMIN_API_GUIDE.md](./ADMIN_API_GUIDE.md)** - Admin endpoints and user management

## Database Migrations

This project uses Alembic for database schema migrations. All migration files are in the `alembic/` directory.

### Common Migration Commands

**With Docker:**

```bash
# Apply all pending migrations
docker exec -it gym_tracker_api sh -c "cd / && alembic upgrade head"

# Create a new migration (auto-generate from model changes)
docker exec -it gym_tracker_api sh -c "cd / && alembic revision --autogenerate -m 'Description of changes'"

# View current migration status
docker exec -it gym_tracker_api sh -c "cd / && alembic current"

# View migration history
docker exec -it gym_tracker_api sh -c "cd / && alembic history"

# Downgrade one migration
docker exec -it gym_tracker_api sh -c "cd / && alembic downgrade -1"
```

**Without Docker:**

```bash
# Apply all pending migrations
alembic upgrade head

# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# View current migration status
alembic current

# View migration history
alembic history

# Downgrade one migration
alembic downgrade -1
```

### Migration Files

The project includes migrations for:
- User authentication and settings (`deb920fb8919`)
- Exercise library with muscle group specificity (`6d038ccb729f`)
- Set-level tracking for workouts (`ed37c08af829`)
- Analytical views for progress tracking (`aaa71891ebea`)
- And more...

### Important Notes

- Always create migrations for schema changes (don't modify the database directly)
- Review auto-generated migrations before applying them
- Test migrations in development before applying to production
- The `alembic/env.py` file is configured to read from `models.Base.metadata`

## To Be Done

The following features are planned but not yet implemented:

### High Priority

- [ ] **Workout Plans/Templates**
  - Create reusable workout templates
  - Schedule workout plans for specific days
  - Copy templates to actual workout sessions
  - _Note: Models exist in `app/models/plan.py` but endpoints are not implemented_

- [ ] **Password Reset via Email**
  - Forgot password functionality
  - Email verification for new accounts
  - Send reset tokens via email

- [ ] **Refresh Tokens**
  - Implement refresh token mechanism
  - Allow longer sessions without requiring re-login
  - Invalidate tokens on logout

### Medium Priority

- [ ] **Exercise Media Support**
  - Upload exercise demonstration videos
  - Add exercise images/thumbnails
  - Store media in cloud storage (S3, Cloudinary, etc.)

- [ ] **Social Features**
  - Share workouts with other users
  - Follow other users
  - Workout feed/timeline
  - Comments and likes on workouts

- [ ] **Scheduled Analytics Refresh**
  - Automatic refresh of materialized views
  - Background task queue (Celery)
  - Cron job for daily/hourly updates

- [ ] **Export Functionality**
  - Export workout data to CSV/Excel
  - Generate PDF workout reports
  - Export analytics charts as images

### Low Priority

- [ ] **Mobile Push Notifications**
  - Workout reminders
  - Goal achievement notifications
  - Friend activity notifications

- [ ] **Advanced Analytics**
  - Machine learning predictions for progress
  - Optimal rest time recommendations
  - Deload week suggestions

- [ ] **Workout Timer Integration**
  - Rest timer between sets
  - Workout duration timer
  - Store timing data with sets

- [ ] **Exercise Categories and Tags**
  - Tag exercises with categories (compound, isolation, etc.)
  - Filter exercises by multiple tags
  - Custom user tags

- [ ] **Multi-language Support**
  - Internationalization (i18n)
  - Support for multiple languages
  - Localized date/time formats

### Infrastructure

- [ ] **CI/CD Pipeline**
  - Automated testing on pull requests
  - Automated deployment to staging/production
  - Docker image builds and publishing

- [ ] **Production Deployment Guide**
  - HTTPS configuration
  - Domain setup
  - Environment-specific settings
  - Backup and recovery procedures

- [ ] **Rate Limiting**
  - API rate limits per user
  - Protection against abuse
  - Redis-based rate limiter

- [ ] **Logging and Monitoring**
  - Structured logging
  - Error tracking (Sentry)
  - Performance monitoring (New Relic, DataDog)
  - Health check endpoints for monitoring systems

## Testing

Run the test suite:

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v
```

View coverage report:
```bash
open htmlcov/index.html  # On macOS
xdg-open htmlcov/index.html  # On Linux
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.

## Support

For questions, issues, or feature requests:
- Open an issue on GitHub
- Check existing documentation guides
- Review the interactive API docs at `/docs`
