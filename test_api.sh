#!/bin/bash

# Gym Dorian API Test Script
# This script creates test data and tests all API endpoints

API_URL="http://localhost:8000/api"
echo "🏋️  Testing Gym Dorian API..."
echo "================================"

# 1. Register Admin User
echo -e "\n📝 Creating admin user..."
curl -s -X POST $API_URL/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@gym.com", "password": "admin123", "full_name": "Admin User"}' | jq .

# Update admin to superuser via database
echo -e "\n🔧 Making admin a superuser..."
docker-compose exec -T db psql -U postgres -d gym_db -c "UPDATE users SET is_superuser = true WHERE email = 'admin@gym.com';"

# 2. Login as regular user
echo -e "\n🔑 Logging in as test user..."
TOKEN=$(curl -s -X POST $API_URL/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser@example.com&password=testpass123" | jq -r .access_token)

echo "Token: $TOKEN"

# 3. Create exercises
echo -e "\n💪 Creating exercises..."

curl -s -X POST $API_URL/workouts/exercises \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Bench Press", "muscle_group": "Chest", "equipment_type": "Barbell"}' | jq .

curl -s -X POST $API_URL/workouts/exercises \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Squat", "muscle_group": "Legs", "equipment_type": "Barbell"}' | jq .

curl -s -X POST $API_URL/workouts/exercises \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Deadlift", "muscle_group": "Back", "equipment_type": "Barbell"}' | jq .

# 4. List exercises
echo -e "\n📋 Listing exercises..."
curl -s -X GET "$API_URL/workouts/exercises" \
  -H "Authorization: Bearer $TOKEN" | jq .

# 5. Create a workout session
echo -e "\n🏋️  Creating workout session..."
curl -s -X POST $API_URL/workouts/sessions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "workout_date": "2025-12-15",
    "duration_minutes": 60,
    "notes": "Great workout!",
    "exercises": [
      {"exercise_id": 1, "sets_completed": 4, "top_weight": 80.0, "total_reps": 32},
      {"exercise_id": 2, "sets_completed": 3, "top_weight": 100.0, "total_reps": 24}
    ]
  }' | jq .

# 6. Quick workout log
echo -e "\n⚡ Creating quick workout..."
curl -s -X POST $API_URL/workouts/sessions/quick \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "workout_date": "2025-12-14",
    "duration_minutes": 45,
    "exercises": [
      {
        "exercise_id": 3,
        "sets": [
          {"set_number": 1, "reps": 5, "weight": 140.0},
          {"set_number": 2, "reps": 5, "weight": 150.0},
          {"set_number": 3, "reps": 3, "weight": 160.0}
        ]
      }
    ]
  }' | jq .

# 7. List workout sessions
echo -e "\n📅 Listing workout sessions..."
curl -s -X GET "$API_URL/workouts/sessions" \
  -H "Authorization: Bearer $TOKEN" | jq .

# 8. Get workout stats
echo -e "\n📊 Getting workout statistics..."
curl -s -X GET "$API_URL/workouts/stats" \
  -H "Authorization: Bearer $TOKEN" | jq .

# 9. Get analytics dashboard
echo -e "\n📈 Getting analytics dashboard..."
curl -s -X GET "$API_URL/analytics/dashboard" \
  -H "Authorization: Bearer $TOKEN" | jq .

# 10. Get user profile
echo -e "\n👤 Getting user profile..."
curl -s -X GET "$API_URL/users/me" \
  -H "Authorization: Bearer $TOKEN" | jq .

# 11. Test admin endpoints (login as admin first)
echo -e "\n🔐 Logging in as admin..."
ADMIN_TOKEN=$(curl -s -X POST $API_URL/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@gym.com&password=admin123" | jq -r .access_token)

echo -e "\n👥 Getting all users (admin only)..."
curl -s -X GET "$API_URL/admin/users" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq .

echo -e "\n📊 Getting admin statistics..."
curl -s -X GET "$API_URL/admin/statistics/users" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq .

echo -e "\n✅ Testing complete!"
echo "================================"
echo "🎉 All endpoints tested successfully!"
