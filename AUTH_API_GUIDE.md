# Authentication API Guide

Complete guide for using the authentication and user management endpoints.

## Table of Contents
- [Setup](#setup)
- [API Endpoints](#api-endpoints)
- [Authentication Flow](#authentication-flow)
- [Testing Examples](#testing-examples)

## Setup

### 1. Install Dependencies
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and update with your settings:
```bash
cp .env.example .env
```

Generate a secure SECRET_KEY:
```bash
openssl rand -hex 32
```

Update your `.env` file:
```env
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/gym_dorian
SECRET_KEY=<your-generated-secret-key>
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 3. Run Database Migrations
```bash
alembic upgrade head
```

### 4. Start the Server
```bash
uvicorn app.main:app --reload
```

The API will be available at: `http://localhost:8000`
API Documentation: `http://localhost:8000/docs`

## API Endpoints

### Authentication Endpoints (`/api/auth`)

#### 1. Register New User
**POST** `/api/auth/register`

Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123",
  "full_name": "John Doe"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-12-15T22:00:00Z",
  "last_login": null
}
```

**Error (400 Bad Request):**
```json
{
  "detail": "Email already registered"
}
```

---

#### 2. Login
**POST** `/api/auth/login`

Login with email and password to receive JWT token.

**Request (Form Data):**
```
username: user@example.com
password: securePassword123
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error (401 Unauthorized):**
```json
{
  "detail": "Incorrect email or password"
}
```

---

#### 3. Test Token
**POST** `/api/auth/test-token`

Test if your JWT token is valid.

**Headers:**
```
Authorization: Bearer <your-jwt-token>
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
  "last_login": "2025-12-15T22:30:00Z"
}
```

---

### User Profile Endpoints (`/api/users`)

All user endpoints require authentication (JWT token in Authorization header).

#### 4. Get Current User Profile
**GET** `/api/users/me`

Get the authenticated user's profile.

**Headers:**
```
Authorization: Bearer <your-jwt-token>
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
  "last_login": "2025-12-15T22:30:00Z"
}
```

---

#### 5. Get Complete User Profile
**GET** `/api/users/me/complete`

Get user profile with settings and goals.

**Headers:**
```
Authorization: Bearer <your-jwt-token>
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
  "last_login": "2025-12-15T22:30:00Z",
  "settings": {
    "id": 1,
    "user_id": 1,
    "weight_unit": "kg",
    "distance_unit": "km",
    "default_rest_time": 90,
    "private_profile": false,
    "email_notifications": true,
    "created_at": "2025-12-15T22:00:00Z",
    "updated_at": "2025-12-15T22:00:00Z"
  },
  "goals": []
}
```

---

#### 6. Update User Profile
**PUT** `/api/users/me`

Update user information.

**Headers:**
```
Authorization: Bearer <your-jwt-token>
```

**Request Body:**
```json
{
  "full_name": "John Smith",
  "password": "newSecurePassword456"
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Smith",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-12-15T22:00:00Z",
  "last_login": "2025-12-15T22:30:00Z"
}
```

---

### User Settings Endpoints

#### 7. Get User Settings
**GET** `/api/users/me/settings`

Get user preferences and settings.

**Headers:**
```
Authorization: Bearer <your-jwt-token>
```

**Response (200 OK):**
```json
{
  "id": 1,
  "user_id": 1,
  "weight_unit": "kg",
  "distance_unit": "km",
  "default_rest_time": 90,
  "private_profile": false,
  "email_notifications": true,
  "created_at": "2025-12-15T22:00:00Z",
  "updated_at": "2025-12-15T22:00:00Z"
}
```

---

#### 8. Update User Settings
**PUT** `/api/users/me/settings`

Update user preferences.

**Headers:**
```
Authorization: Bearer <your-jwt-token>
```

**Request Body:**
```json
{
  "weight_unit": "lbs",
  "default_rest_time": 60,
  "private_profile": true
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "user_id": 1,
  "weight_unit": "lbs",
  "distance_unit": "km",
  "default_rest_time": 60,
  "private_profile": true,
  "email_notifications": true,
  "created_at": "2025-12-15T22:00:00Z",
  "updated_at": "2025-12-15T22:45:00Z"
}
```

---

### User Goals Endpoints

#### 9. Get All User Goals
**GET** `/api/users/me/goals`

Get all fitness goals for the authenticated user.

**Headers:**
```
Authorization: Bearer <your-jwt-token>
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "goal_type": "strength",
    "title": "Bench Press 100kg",
    "description": "Increase bench press to 100kg by end of year",
    "target_value": 100.0,
    "current_value": 80.0,
    "target_date": "2025-12-31T00:00:00Z",
    "status": "active",
    "created_at": "2025-12-15T22:00:00Z",
    "updated_at": "2025-12-15T22:00:00Z",
    "completed_at": null
  }
]
```

---

#### 10. Create New Goal
**POST** `/api/users/me/goals`

Create a new fitness goal.

**Headers:**
```
Authorization: Bearer <your-jwt-token>
```

**Request Body:**
```json
{
  "goal_type": "strength",
  "title": "Bench Press 100kg",
  "description": "Increase bench press to 100kg by end of year",
  "target_value": 100.0,
  "current_value": 80.0,
  "target_date": "2025-12-31T00:00:00Z"
}
```

**Goal Types:**
- `strength` - Increase max weight
- `muscle_gain` - Build muscle mass
- `weight_loss` - Lose body weight
- `endurance` - Improve cardiovascular endurance
- `consistency` - Maintain workout routine
- `custom` - User-defined goal

**Response (201 Created):**
```json
{
  "id": 1,
  "user_id": 1,
  "goal_type": "strength",
  "title": "Bench Press 100kg",
  "description": "Increase bench press to 100kg by end of year",
  "target_value": 100.0,
  "current_value": 80.0,
  "target_date": "2025-12-31T00:00:00Z",
  "status": "active",
  "created_at": "2025-12-15T22:00:00Z",
  "updated_at": "2025-12-15T22:00:00Z",
  "completed_at": null
}
```

---

#### 11. Get Specific Goal
**GET** `/api/users/me/goals/{goal_id}`

Get a specific goal by ID.

**Headers:**
```
Authorization: Bearer <your-jwt-token>
```

**Response (200 OK):**
```json
{
  "id": 1,
  "user_id": 1,
  "goal_type": "strength",
  "title": "Bench Press 100kg",
  "description": "Increase bench press to 100kg by end of year",
  "target_value": 100.0,
  "current_value": 85.0,
  "target_date": "2025-12-31T00:00:00Z",
  "status": "active",
  "created_at": "2025-12-15T22:00:00Z",
  "updated_at": "2025-12-15T23:00:00Z",
  "completed_at": null
}
```

---

#### 12. Update Goal
**PUT** `/api/users/me/goals/{goal_id}`

Update goal progress or information.

**Headers:**
```
Authorization: Bearer <your-jwt-token>
```

**Request Body:**
```json
{
  "current_value": 85.0,
  "status": "active"
}
```

**Goal Statuses:**
- `active` - Currently working on
- `completed` - Goal achieved
- `abandoned` - No longer pursuing

**Response (200 OK):**
```json
{
  "id": 1,
  "user_id": 1,
  "goal_type": "strength",
  "title": "Bench Press 100kg",
  "description": "Increase bench press to 100kg by end of year",
  "target_value": 100.0,
  "current_value": 85.0,
  "target_date": "2025-12-31T00:00:00Z",
  "status": "active",
  "created_at": "2025-12-15T22:00:00Z",
  "updated_at": "2025-12-15T23:00:00Z",
  "completed_at": null
}
```

---

#### 13. Delete Goal
**DELETE** `/api/users/me/goals/{goal_id}`

Delete a fitness goal.

**Headers:**
```
Authorization: Bearer <your-jwt-token>
```

**Response (204 No Content)**

---

## Authentication Flow

### 1. Register or Login
```bash
# Register new user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securePassword123",
    "full_name": "John Doe"
  }'

# Login to get token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=securePassword123"
```

### 2. Save the Token
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 3. Use Token in Subsequent Requests
```bash
curl -X GET http://localhost:8000/api/users/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## Testing Examples

### Using cURL

```bash
# 1. Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123",
    "full_name": "Test User"
  }'

# 2. Login
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=testpass123" \
  | jq -r '.access_token')

# 3. Get profile
curl -X GET http://localhost:8000/api/users/me \
  -H "Authorization: Bearer $TOKEN"

# 4. Create a goal
curl -X POST http://localhost:8000/api/users/me/goals \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "goal_type": "strength",
    "title": "Squat 150kg",
    "target_value": 150.0,
    "current_value": 120.0
  }'

# 5. Update settings
curl -X PUT http://localhost:8000/api/users/me/settings \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "weight_unit": "lbs",
    "default_rest_time": 60
  }'
```

### Using Python Requests

```python
import requests

BASE_URL = "http://localhost:8000/api"

# Register
response = requests.post(
    f"{BASE_URL}/auth/register",
    json={
        "email": "test@example.com",
        "password": "testpass123",
        "full_name": "Test User"
    }
)
print(response.json())

# Login
response = requests.post(
    f"{BASE_URL}/auth/login",
    data={
        "username": "test@example.com",
        "password": "testpass123"
    }
)
token = response.json()["access_token"]

# Use token for authenticated requests
headers = {"Authorization": f"Bearer {token}"}

# Get profile
response = requests.get(f"{BASE_URL}/users/me", headers=headers)
print(response.json())

# Create goal
response = requests.post(
    f"{BASE_URL}/users/me/goals",
    headers=headers,
    json={
        "goal_type": "strength",
        "title": "Deadlift 200kg",
        "target_value": 200.0,
        "current_value": 160.0
    }
)
print(response.json())
```

## Error Handling

### Common Error Responses

**401 Unauthorized:**
```json
{
  "detail": "Could not validate credentials"
}
```

**400 Bad Request:**
```json
{
  "detail": "Email already registered"
}
```

**404 Not Found:**
```json
{
  "detail": "Goal not found"
}
```

**422 Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

## Security Notes

1. **HTTPS Required in Production**: Always use HTTPS in production to protect JWT tokens
2. **Secret Key**: Use a strong, randomly generated SECRET_KEY in production
3. **Token Expiration**: Tokens expire based on ACCESS_TOKEN_EXPIRE_MINUTES setting
4. **Password Requirements**: Minimum 8 characters (can be customized in schemas)
5. **CORS**: Update allowed origins in production (currently set to "*" for development)

## Next Steps

- Integrate user authentication with workout logging endpoints
- Add password reset functionality
- Implement refresh tokens for longer sessions
- Add email verification for new users
- Create admin endpoints for user management
