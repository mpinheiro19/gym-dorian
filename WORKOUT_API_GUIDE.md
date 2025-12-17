```markdown
# Workout Logging API Guide

Complete guide for logging workouts and tracking exercises.

## Table of Contents
- [Overview](#overview)
- [Quick Start](#quick-start)
- [Exercise Management](#exercise-management)
- [Workout Logging](#workout-logging)
- [Use Cases & Examples](#use-cases--examples)

---

## Overview

The Workout Logging API allows users to:
- Manage exercise library (create, update, list exercises)
- Log workout sessions with exercises
- Track sets, reps, and weights
- Query workout history
- Copy previous workouts

All endpoints require authentication.

---

## Quick Start

### 1. Create Your First Exercise

```bash
# Login first
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=password" \
  | jq -r '.access_token')

# Create Bench Press exercise
curl -X POST "http://localhost:8000/api/workouts/exercises" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Bench Press",
    "muscle_group": "Chest",
    "equipment_type": "Barbell"
  }'
```

### 2. Log Your First Workout

**Method 1: Standard Logging**
```bash
curl -X POST "http://localhost:8000/api/workouts/sessions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "workout_date": "2025-12-15",
    "duration_minutes": 60,
    "notes": "Great chest day!",
    "exercises": [
      {
        "exercise_id": 1,
        "sets_completed": 3,
        "top_weight": 80.0,
        "total_reps": 30
      }
    ]
  }'
```

**Method 2: Quick Logging (Easier!)**
```bash
curl -X POST "http://localhost:8000/api/workouts/sessions/quick" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "workout_date": "2025-12-15",
    "duration_minutes": 60,
    "exercises": [
      {
        "exercise_id": 1,
        "sets": [
          {"set_number": 1, "reps": 10, "weight": 80.0},
          {"set_number": 2, "reps": 10, "weight": 80.0},
          {"set_number": 3, "reps": 10, "weight": 80.0}
        ]
      }
    ]
  }'
```

The quick logging method automatically calculates:
- `sets_completed` = 3 (count of sets)
- `top_weight` = 80.0 (max weight)
- `total_reps` = 30 (sum of reps)

---

## Exercise Management

### List All Exercises

**GET** `/api/workouts/exercises`

**Query Parameters:**
- `skip` (int, default=0): Pagination offset
- `limit` (int, default=100): Max results
- `muscle_group` (string): Filter by muscle group
- `search` (string): Search exercise name

**Examples:**
```bash
# Get all exercises
curl -X GET "http://localhost:8000/api/workouts/exercises" \
  -H "Authorization: Bearer $TOKEN"

# Filter by muscle group
curl -X GET "http://localhost:8000/api/workouts/exercises?muscle_group=Chest" \
  -H "Authorization: Bearer $TOKEN"

# Search by name
curl -X GET "http://localhost:8000/api/workouts/exercises?search=press" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Bench Press",
    "muscle_group": "Chest",
    "equipment_type": "Barbell"
  },
  {
    "id": 2,
    "name": "Squat",
    "muscle_group": "Legs",
    "equipment_type": "Barbell"
  }
]
```

---

### Create Exercise

**POST** `/api/workouts/exercises`

**Request Body:**
```json
{
  "name": "Deadlift",
  "muscle_group": "Back",
  "equipment_type": "Barbell"
}
```

**Response (201 Created):**
```json
{
  "id": 3,
  "name": "Deadlift",
  "muscle_group": "Back",
  "equipment_type": "Barbell"
}
```

**Common Muscle Groups:**
- Chest, Back, Shoulders, Legs, Arms, Core, Cardio

**Common Equipment Types:**
- Barbell, Dumbbell, Machine, Bodyweight, Cable, Kettlebell

---

### Update Exercise

**PUT** `/api/workouts/exercises/{exercise_id}`

```bash
curl -X PUT "http://localhost:8000/api/workouts/exercises/1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "muscle_group": "Upper Chest"
  }'
```

---

### Delete Exercise

**DELETE** `/api/workouts/exercises/{exercise_id}`

```bash
curl -X DELETE "http://localhost:8000/api/workouts/exercises/1" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Workout Logging

### List Workout Sessions

**GET** `/api/workouts/sessions`

**Query Parameters:**
- `skip`, `limit`: Pagination
- `start_date`, `end_date`: Date range filter

**Examples:**
```bash
# Get last 10 workouts
curl -X GET "http://localhost:8000/api/workouts/sessions?limit=10" \
  -H "Authorization: Bearer $TOKEN"

# Get workouts from December
curl -X GET "http://localhost:8000/api/workouts/sessions?start_date=2025-12-01&end_date=2025-12-31" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "workout_date": "2025-12-15",
    "duration_minutes": 60,
    "notes": "Great workout!",
    "exercises_done": [
      {
        "id": 1,
        "session_id": 1,
        "exercise_id": 1,
        "sets_completed": 3,
        "top_weight": 80.0,
        "total_reps": 30,
        "exercise": {
          "id": 1,
          "name": "Bench Press",
          "muscle_group": "Chest",
          "equipment_type": "Barbell"
        }
      }
    ]
  }
]
```

---

### Get Specific Workout

**GET** `/api/workouts/sessions/{workout_id}`

```bash
curl -X GET "http://localhost:8000/api/workouts/sessions/1" \
  -H "Authorization: Bearer $TOKEN"
```

---

### Create Workout Session

**POST** `/api/workouts/sessions`

**Standard Method:**
```json
{
  "workout_date": "2025-12-15",
  "duration_minutes": 90,
  "notes": "Push day",
  "exercises": [
    {
      "exercise_id": 1,
      "sets_completed": 4,
      "top_weight": 100.0,
      "total_reps": 32
    },
    {
      "exercise_id": 2,
      "sets_completed": 3,
      "top_weight": 30.0,
      "total_reps": 30
    }
  ]
}
```

**Quick Method (Recommended):**

**POST** `/api/workouts/sessions/quick`

```json
{
  "workout_date": "2025-12-15",
  "duration_minutes": 90,
  "notes": "Push day",
  "exercises": [
    {
      "exercise_id": 1,
      "sets": [
        {"set_number": 1, "reps": 8, "weight": 100.0, "rpe": 8},
        {"set_number": 2, "reps": 8, "weight": 100.0, "rpe": 9},
        {"set_number": 3, "reps": 8, "weight": 100.0, "rpe": 9},
        {"set_number": 4, "reps": 8, "weight": 100.0, "rpe": 10}
      ]
    },
    {
      "exercise_id": 2,
      "sets": [
        {"set_number": 1, "reps": 10, "weight": 30.0},
        {"set_number": 2, "reps": 10, "weight": 30.0},
        {"set_number": 3, "reps": 10, "weight": 30.0}
      ]
    }
  ]
}
```

**Set Details:**
- `set_number`: Order of the set
- `reps`: Repetitions completed
- `weight`: Weight used (kg or lbs)
- `rpe`: Rate of Perceived Exertion (1-10) - optional
- `notes`: Set-specific notes - optional

---

### Update Workout Session

**PUT** `/api/workouts/sessions/{workout_id}`

Update session-level fields (date, duration, notes):

```bash
curl -X PUT "http://localhost:8000/api/workouts/sessions/1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "duration_minutes": 75,
    "notes": "Updated: felt stronger today!"
  }'
```

---

### Delete Workout Session

**DELETE** `/api/workouts/sessions/{workout_id}`

```bash
curl -X DELETE "http://localhost:8000/api/workouts/sessions/1" \
  -H "Authorization: Bearer $TOKEN"
```

---

### Copy Previous Workout

**POST** `/api/workouts/sessions/copy`

Repeat a previous workout on a new date:

```bash
curl -X POST "http://localhost:8000/api/workouts/sessions/copy" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_workout_id": 1,
    "new_date": "2025-12-16",
    "copy_notes": false
  }'
```

---

### Add Exercise to Workout

**POST** `/api/workouts/sessions/{workout_id}/exercises`

Add an exercise to an existing workout:

```bash
curl -X POST "http://localhost:8000/api/workouts/sessions/1/exercises" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "exercise_id": 3,
    "sets_completed": 3,
    "top_weight": 150.0,
    "total_reps": 15
  }'
```

---

### Update Logged Exercise

**PUT** `/api/workouts/exercises/logged/{log_exercise_id}`

Modify a specific exercise within a workout:

```bash
curl -X PUT "http://localhost:8000/api/workouts/exercises/logged/1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "top_weight": 85.0,
    "total_reps": 32
  }'
```

---

### Delete Logged Exercise

**DELETE** `/api/workouts/exercises/logged/{log_exercise_id}`

Remove an exercise from a workout:

```bash
curl -X DELETE "http://localhost:8000/api/workouts/exercises/logged/1" \
  -H "Authorization: Bearer $TOKEN"
```

---

### Get Workout Statistics

**GET** `/api/workouts/stats`

Get aggregate statistics:

```bash
# All-time stats
curl -X GET "http://localhost:8000/api/workouts/stats" \
  -H "Authorization: Bearer $TOKEN"

# Stats for a date range
curl -X GET "http://localhost:8000/api/workouts/stats?start_date=2025-12-01&end_date=2025-12-31" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "total_workouts": 45,
  "total_duration_minutes": 3375,
  "total_exercises_logged": 180,
  "total_volume": 125600.5,
  "unique_exercises": 12,
  "avg_workout_duration": 75.0
}
```

---

## Use Cases & Examples

### Use Case 1: Mobile App Workout Logging

```javascript
// User completes a workout in the app
const workout = {
  workout_date: new Date().toISOString().split('T')[0],
  duration_minutes: 75,
  exercises: [
    {
      exercise_id: 1, // Bench Press
      sets: [
        { set_number: 1, reps: 10, weight: 80, rpe: 7 },
        { set_number: 2, reps: 10, weight: 85, rpe: 8 },
        { set_number: 3, reps: 8, weight: 90, rpe: 9 },
        { set_number: 4, reps: 6, weight: 95, rpe: 10 }
      ]
    },
    {
      exercise_id: 2, // Incline Press
      sets: [
        { set_number: 1, reps: 10, weight: 30, rpe: 7 },
        { set_number: 2, reps: 10, weight: 30, rpe: 8 },
        { set_number: 3, reps: 10, weight: 30, rpe: 8 }
      ]
    }
  ]
};

// Log workout
const response = await fetch('/api/workouts/sessions/quick', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(workout)
});

const result = await response.json();
console.log(`Workout ${result.id} logged successfully!`);
```

---

### Use Case 2: Repeating a Routine

```python
import requests

BASE_URL = "http://localhost:8000/api"
headers = {"Authorization": f"Bearer {token}"}

# Get my last workout
workouts = requests.get(
    f"{BASE_URL}/workouts/sessions",
    params={"limit": 1},
    headers=headers
).json()

last_workout_id = workouts[0]['id']

# Copy it to today
today = "2025-12-16"
new_workout = requests.post(
    f"{BASE_URL}/workouts/sessions/copy",
    headers=headers,
    json={
        "source_workout_id": last_workout_id,
        "new_date": today,
        "copy_notes": False
    }
).json()

print(f"Copied workout {last_workout_id} to {today}")
print(f"New workout ID: {new_workout['id']}")
```

---

### Use Case 3: Building an Exercise Library

```python
# Define your workout program
exercises = [
    {"name": "Bench Press", "muscle_group": "Chest", "equipment_type": "Barbell"},
    {"name": "Squat", "muscle_group": "Legs", "equipment_type": "Barbell"},
    {"name": "Deadlift", "muscle_group": "Back", "equipment_type": "Barbell"},
    {"name": "Overhead Press", "muscle_group": "Shoulders", "equipment_type": "Barbell"},
    {"name": "Barbell Row", "muscle_group": "Back", "equipment_type": "Barbell"},
    {"name": "Pull-ups", "muscle_group": "Back", "equipment_type": "Bodyweight"},
    {"name": "Dips", "muscle_group": "Chest", "equipment_type": "Bodyweight"},
]

# Create all exercises
for exercise in exercises:
    response = requests.post(
        f"{BASE_URL}/workouts/exercises",
        headers=headers,
        json=exercise
    )
    if response.status_code == 201:
        result = response.json()
        print(f"Created: {result['name']} (ID: {result['id']})")
```

---

### Use Case 4: Tracking Progress on Bench Press

```python
# Get all workouts where I did bench press (exercise_id=1)
workouts = requests.get(
    f"{BASE_URL}/workouts/sessions",
    params={"limit": 100},
    headers=headers
).json()

# Extract bench press data
bench_data = []
for workout in workouts:
    for exercise in workout['exercises_done']:
        if exercise['exercise']['name'] == 'Bench Press':
            bench_data.append({
                'date': workout['workout_date'],
                'max_weight': exercise['top_weight'],
                'total_reps': exercise['total_reps']
            })

# Plot progress
import matplotlib.pyplot as plt
import pandas as pd

df = pd.DataFrame(bench_data)
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date')

plt.figure(figsize=(10, 6))
plt.plot(df['date'], df['max_weight'], marker='o')
plt.xlabel('Date')
plt.ylabel('Weight (kg)')
plt.title('Bench Press Progress')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
```

---

### Use Case 5: Weekly Report

```python
from datetime import datetime, timedelta

# Get last 7 days
end_date = datetime.now().date()
start_date = end_date - timedelta(days=7)

stats = requests.get(
    f"{BASE_URL}/workouts/stats",
    params={
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat()
    },
    headers=headers
).json()

print("📊 Weekly Report")
print(f"Workouts: {stats['total_workouts']}")
print(f"Total Time: {stats['total_duration_minutes']} min")
print(f"Total Volume: {stats['total_volume']:.0f} kg")
print(f"Exercises: {stats['unique_exercises']} unique")
```

---

## Integration with Analytics

After logging workouts, the data flows into the analytics system:

1. **Log Workout** → Data saved to `workout_sessions` and `log_exercises` tables
2. **Refresh Analytics** → Run `/api/analytics/refresh-views` (admin) or wait for scheduled refresh
3. **View Progress** → Use `/api/analytics/*` endpoints to see trends

**Example Workflow:**
```bash
# 1. Log workout
curl -X POST "/api/workouts/sessions/quick" -d '{...}'

# 2. Refresh analytics (as admin, or wait for cron)
curl -X POST "/api/analytics/refresh-views" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# 3. View progress
curl -X GET "/api/analytics/progress/exercise/1?days=90" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Best Practices

### 1. Use Quick Logging for Detailed Tracking
The quick logging endpoint is easier and provides set-by-set details:
```json
{
  "exercises": [
    {
      "exercise_id": 1,
      "sets": [
        {"set_number": 1, "reps": 10, "weight": 80, "rpe": 7},
        {"set_number": 2, "reps": 10, "weight": 80, "rpe": 8}
      ]
    }
  ]
}
```

### 2. Log Workouts Immediately
Don't wait - log right after finishing to capture accurate data.

### 3. Be Consistent with Exercise Names
Create exercises once, reuse them. Don't create "Bench Press" and "bench press" separately.

### 4. Track RPE When Possible
Rate of Perceived Exertion helps track intensity over time.

### 5. Use Notes for Context
Add notes about how you felt, modifications, or anything unusual.

---

## Error Handling

**400 Bad Request:**
```json
{
  "detail": "Exercise with ID 999 not found"
}
```

**404 Not Found:**
```json
{
  "detail": "Workout session not found"
}
```

**422 Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "exercises", 0, "sets_completed"],
      "msg": "ensure this value is greater than or equal to 1",
      "type": "value_error.number.not_ge"
    }
  ]
}
```

---

## Next Steps

Now that you can log workouts:
1. Build a mobile app or web frontend
2. Set up automated analytics refresh
3. Create workout templates for routines
4. Add exercise video/image support
5. Implement social features (share workouts)

For analytics and progress tracking, see [ANALYTICS_API_GUIDE.md](./ANALYTICS_API_GUIDE.md).
```

