# Admin API Guide

Complete guide for admin/superuser endpoints for managing users and viewing system statistics.

## Table of Contents
- [Authentication](#authentication)
- [User Management](#user-management)
- [Statistics & Analytics](#statistics--analytics)
- [Testing Examples](#testing-examples)

## Authentication

All admin endpoints require **superuser authentication**. You must:
1. Have a user account with `is_superuser=true`
2. Include a valid JWT token in the Authorization header

### Creating the First Superuser

You can create a superuser directly in the database or through a migration script:

```python
# Create first superuser (run this script once)
from app.database import SessionLocal
from app.crud.admin import create_user_admin
from app.schemas.user_schema import UserCreate

db = SessionLocal()
user_create = UserCreate(
    email="admin@example.com",
    password="secure_admin_password",
    full_name="Admin User"
)
admin_user = create_user_admin(db, user_create, is_superuser=True)
db.close()

print(f"Superuser created: {admin_user.email}")
```

Or use SQL directly:
```sql
-- After running migrations and creating a regular user
UPDATE users SET is_superuser = true WHERE email = 'admin@example.com';
```

### Login as Admin

```bash
# Login to get admin token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=secure_admin_password"
```

Use the returned token for all admin requests:
```bash
export ADMIN_TOKEN="your-jwt-token-here"
```

---

## User Management

All endpoints are under `/api/admin/users` and require superuser authentication.

### 1. List All Users (with Pagination & Filtering)

**GET** `/api/admin/users`

Get a paginated list of all users with optional filtering.

**Query Parameters:**
- `skip` (int, default=0): Number of records to skip
- `limit` (int, default=100, max=1000): Maximum records to return
- `is_active` (bool, optional): Filter by active status
- `is_superuser` (bool, optional): Filter by superuser status
- `search` (string, optional): Search by email or name

**Example Requests:**

```bash
# Get all users (first 100)
curl -X GET "http://localhost:8000/api/admin/users" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Get inactive users
curl -X GET "http://localhost:8000/api/admin/users?is_active=false" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Search for users
curl -X GET "http://localhost:8000/api/admin/users?search=john" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Pagination (skip first 20, get next 10)
curl -X GET "http://localhost:8000/api/admin/users?skip=20&limit=10" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": 1,
      "email": "user@example.com",
      "full_name": "John Doe",
      "is_active": true,
      "is_superuser": false,
      "created_at": "2025-12-15T22:00:00Z",
      "updated_at": "2025-12-15T22:00:00Z",
      "last_login": "2025-12-15T23:00:00Z"
    }
  ],
  "total": 50,
  "skip": 0,
  "limit": 100,
  "has_more": false
}
```

---

### 2. Get User by ID

**GET** `/api/admin/users/{user_id}`

Get detailed information about a specific user.

**Example:**
```bash
curl -X GET "http://localhost:8000/api/admin/users/1" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-12-15T22:00:00Z",
  "updated_at": "2025-12-15T22:00:00Z",
  "last_login": "2025-12-15T23:00:00Z"
}
```

**Error (404 Not Found):**
```json
{
  "detail": "User not found"
}
```

---

### 3. Create User (Admin)

**POST** `/api/admin/users`

Create a new user account. Can create superuser accounts.

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "password": "securePassword123",
  "full_name": "New User",
  "is_superuser": false,
  "is_active": true
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/admin/users" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "securePassword123",
    "full_name": "New User",
    "is_superuser": false,
    "is_active": true
  }'
```

**Response (201 Created):**
```json
{
  "id": 2,
  "email": "newuser@example.com",
  "full_name": "New User",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-12-15T23:30:00Z",
  "updated_at": "2025-12-15T23:30:00Z",
  "last_login": null
}
```

---

### 4. Update User

**PUT** `/api/admin/users/{user_id}`

Update user information including status fields.

**Request Body (all fields optional):**
```json
{
  "email": "newemail@example.com",
  "full_name": "Updated Name",
  "password": "newPassword123",
  "is_active": true,
  "is_superuser": false
}
```

**Example:**
```bash
curl -X PUT "http://localhost:8000/api/admin/users/2" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Updated Name",
    "is_active": false
  }'
```

**Response (200 OK):**
```json
{
  "id": 2,
  "email": "newuser@example.com",
  "full_name": "Updated Name",
  "is_active": false,
  "is_superuser": false,
  "created_at": "2025-12-15T23:30:00Z",
  "updated_at": "2025-12-16T00:00:00Z",
  "last_login": null
}
```

---

### 5. Toggle User Active Status

**POST** `/api/admin/users/{user_id}/toggle-active`

Quickly toggle a user's active/inactive status.

**Example:**
```bash
curl -X POST "http://localhost:8000/api/admin/users/2/toggle-active" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Response (200 OK):**
```json
{
  "id": 2,
  "email": "newuser@example.com",
  "full_name": "Updated Name",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-12-15T23:30:00Z",
  "updated_at": "2025-12-16T00:05:00Z",
  "last_login": null
}
```

**Error (400 Bad Request):**
```json
{
  "detail": "Cannot deactivate your own account"
}
```

---

### 6. Delete User

**DELETE** `/api/admin/users/{user_id}`

Permanently delete a user and all related data (cascading delete).

**Warning:** This action is irreversible and will delete:
- User account
- User settings
- User goals
- Workout sessions
- Exercise logs

**Example:**
```bash
curl -X DELETE "http://localhost:8000/api/admin/users/2" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Response (204 No Content)**

**Error (400 Bad Request):**
```json
{
  "detail": "Cannot delete your own account"
}
```

---

### 7. Get User Activity Details

**GET** `/api/admin/users/{user_id}/activity`

Get detailed activity information for a specific user.

**Example:**
```bash
curl -X GET "http://localhost:8000/api/admin/users/1/activity" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Response (200 OK):**
```json
{
  "user_id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "account_created": "2025-12-15T22:00:00Z",
  "last_login": "2025-12-15T23:00:00Z",
  "is_active": true,
  "total_workouts": 25,
  "total_workout_duration_minutes": 1875,
  "last_workout_date": "2025-12-15",
  "active_goals": 3,
  "completed_goals": 1
}
```

---

## Statistics & Analytics

All statistics endpoints are under `/api/admin/statistics`.

### 8. User Statistics

**GET** `/api/admin/statistics/users`

Get overall user statistics.

**Example:**
```bash
curl -X GET "http://localhost:8000/api/admin/statistics/users" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Response (200 OK):**
```json
{
  "total_users": 150,
  "active_users": 142,
  "inactive_users": 8,
  "superusers": 2,
  "new_users_last_30_days": 23,
  "active_users_last_7_days": 87
}
```

---

### 9. Workout Statistics

**GET** `/api/admin/statistics/workouts`

Get overall workout statistics.

**Example:**
```bash
curl -X GET "http://localhost:8000/api/admin/statistics/workouts" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Response (200 OK):**
```json
{
  "total_workouts": 3450,
  "total_exercises_logged": 15230,
  "workouts_last_30_days": 427,
  "most_active_users": [
    {
      "email": "athlete@example.com",
      "full_name": "Top Athlete",
      "workout_count": 68
    },
    {
      "email": "user2@example.com",
      "full_name": "Dedicated User",
      "workout_count": 54
    }
  ],
  "popular_exercises": [
    {
      "exercise": "Bench Press",
      "times_logged": 892
    },
    {
      "exercise": "Squat",
      "times_logged": 845
    },
    {
      "exercise": "Deadlift",
      "times_logged": 723
    }
  ]
}
```

---

### 10. Goal Statistics

**GET** `/api/admin/statistics/goals`

Get overall goal statistics.

**Example:**
```bash
curl -X GET "http://localhost:8000/api/admin/statistics/goals" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Response (200 OK):**
```json
{
  "total_goals": 342,
  "active_goals": 245,
  "completed_goals": 78,
  "abandoned_goals": 19,
  "completion_rate": 22.81,
  "goals_by_type": [
    {
      "type": "strength",
      "count": 156
    },
    {
      "type": "weight_loss",
      "count": 89
    },
    {
      "type": "muscle_gain",
      "count": 67
    },
    {
      "type": "endurance",
      "count": 23
    },
    {
      "type": "consistency",
      "count": 7
    }
  ]
}
```

---

### 11. Dashboard Statistics

**GET** `/api/admin/statistics/dashboard`

Get all statistics combined in a single response.

**Example:**
```bash
curl -X GET "http://localhost:8000/api/admin/statistics/dashboard" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Response (200 OK):**
```json
{
  "users": {
    "total_users": 150,
    "active_users": 142,
    "inactive_users": 8,
    "superusers": 2,
    "new_users_last_30_days": 23,
    "active_users_last_7_days": 87
  },
  "workouts": {
    "total_workouts": 3450,
    "total_exercises_logged": 15230,
    "workouts_last_30_days": 427,
    "most_active_users": [...],
    "popular_exercises": [...]
  },
  "goals": {
    "total_goals": 342,
    "active_goals": 245,
    "completed_goals": 78,
    "abandoned_goals": 19,
    "completion_rate": 22.81,
    "goals_by_type": [...]
  }
}
```

---

## Testing Examples

### Complete Admin Workflow

```bash
#!/bin/bash

# 1. Login as admin
ADMIN_TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=admin_password" \
  | jq -r '.access_token')

echo "Admin token: $ADMIN_TOKEN"

# 2. View dashboard statistics
echo "\n=== Dashboard Statistics ==="
curl -s -X GET "http://localhost:8000/api/admin/statistics/dashboard" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq

# 3. List all users
echo "\n=== All Users ==="
curl -s -X GET "http://localhost:8000/api/admin/users?limit=5" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq

# 4. Search for a specific user
echo "\n=== Search Users ==="
curl -s -X GET "http://localhost:8000/api/admin/users?search=john" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq

# 5. Create a new user
echo "\n=== Create New User ==="
NEW_USER=$(curl -s -X POST "http://localhost:8000/api/admin/users" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "testpass123",
    "full_name": "Test User",
    "is_active": true
  }' | jq)

echo "$NEW_USER"
USER_ID=$(echo "$NEW_USER" | jq -r '.id')

# 6. Get user activity
echo "\n=== User Activity for ID: $USER_ID ==="
curl -s -X GET "http://localhost:8000/api/admin/users/$USER_ID/activity" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq

# 7. Update user
echo "\n=== Update User ==="
curl -s -X PUT "http://localhost:8000/api/admin/users/$USER_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Updated Test User"
  }' | jq

# 8. Toggle user active status
echo "\n=== Toggle User Active Status ==="
curl -s -X POST "http://localhost:8000/api/admin/users/$USER_ID/toggle-active" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq

# 9. Get inactive users
echo "\n=== Inactive Users ==="
curl -s -X GET "http://localhost:8000/api/admin/users?is_active=false&limit=5" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq

# 10. View user statistics
echo "\n=== User Statistics ==="
curl -s -X GET "http://localhost:8000/api/admin/statistics/users" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq
```

### Python Example

```python
import requests

BASE_URL = "http://localhost:8000/api"

# Login as admin
response = requests.post(
    f"{BASE_URL}/auth/login",
    data={
        "username": "admin@example.com",
        "password": "admin_password"
    }
)
admin_token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {admin_token}"}

# Get dashboard statistics
dashboard = requests.get(
    f"{BASE_URL}/admin/statistics/dashboard",
    headers=headers
).json()
print("Dashboard Stats:", dashboard)

# List all users
users = requests.get(
    f"{BASE_URL}/admin/users",
    params={"limit": 10},
    headers=headers
).json()
print(f"Total users: {users['total']}")
print(f"Returned: {len(users['items'])} users")

# Create a new user
new_user = requests.post(
    f"{BASE_URL}/admin/users",
    headers=headers,
    json={
        "email": "testuser@example.com",
        "password": "testpass123",
        "full_name": "Test User",
        "is_active": True
    }
).json()
print("Created user:", new_user)

# Get user activity
activity = requests.get(
    f"{BASE_URL}/admin/users/{new_user['id']}/activity",
    headers=headers
).json()
print("User activity:", activity)

# Search users
search_results = requests.get(
    f"{BASE_URL}/admin/users",
    params={"search": "test"},
    headers=headers
).json()
print(f"Found {len(search_results['items'])} users matching 'test'")
```

---

## Authorization & Security

### Access Control

- All admin endpoints require `is_superuser=true`
- Attempting to access admin endpoints as a regular user returns `403 Forbidden`
- Invalid or expired tokens return `401 Unauthorized`

**Example Error (403 Forbidden):**
```json
{
  "detail": "Not enough permissions"
}
```

### Protection Against Self-Harm

Admins cannot:
- Delete their own account
- Deactivate their own account (via toggle)

These protections prevent accidental lockouts.

### Audit Trail

Consider implementing audit logging for admin actions:
- User creation/updates/deletions
- Status changes
- Login attempts

---

## Common Use Cases

### 1. Deactivate Inactive Users

```bash
# Find users who haven't logged in recently
curl -X GET "http://localhost:8000/api/admin/users?is_active=true" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | jq '.items[] | select(.last_login == null or .last_login < "2025-11-01")'

# Deactivate a specific user
curl -X POST "http://localhost:8000/api/admin/users/5/toggle-active" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### 2. Monitor System Growth

```bash
# Get statistics regularly
curl -X GET "http://localhost:8000/api/admin/statistics/dashboard" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  > statistics_$(date +%Y%m%d).json
```

### 3. Find Most Engaged Users

```bash
# Top users by workout count
curl -X GET "http://localhost:8000/api/admin/statistics/workouts" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | jq '.most_active_users'
```

### 4. Bulk User Management

```python
import requests

BASE_URL = "http://localhost:8000/api"
headers = {"Authorization": f"Bearer {admin_token}"}

# Get all inactive users
inactive_users = requests.get(
    f"{BASE_URL}/admin/users",
    params={"is_active": False, "limit": 1000},
    headers=headers
).json()['items']

# Delete users inactive for > 6 months
from datetime import datetime, timedelta
cutoff = datetime.utcnow() - timedelta(days=180)

for user in inactive_users:
    last_login = datetime.fromisoformat(user['last_login'].replace('Z', '+00:00')) if user['last_login'] else user['created_at']
    if last_login < cutoff:
        print(f"Deleting inactive user: {user['email']}")
        requests.delete(
            f"{BASE_URL}/admin/users/{user['id']}",
            headers=headers
        )
```

---

## Next Steps

- Implement audit logging for admin actions
- Add export functionality (CSV/JSON) for user lists
- Create scheduled reports for system statistics
- Add email notifications for admin alerts
- Implement role-based access (multiple admin levels)
