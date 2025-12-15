# Analytics API Guide

Complete guide for workout progress tracking and analytics endpoints.

## Table of Contents
- [Overview](#overview)
- [Database Views](#database-views)
- [API Endpoints](#api-endpoints)
- [Use Cases & Examples](#use-cases--examples)
- [Maintenance](#maintenance)

---

## Overview

The Analytics API provides powerful insights into workout progress, helping users track their fitness journey through data visualization and intelligent recommendations.

### Key Features

✓ **Exercise Progress Tracking** - Monitor weight, reps, and volume over time
✓ **Volume Analysis** - Weekly and monthly workout volume trends
✓ **Personal Records** - Track maximum weights achieved
✓ **Muscle Group Distribution** - Identify training imbalances
✓ **Smart Insights** - AI-generated recommendations and achievements
✓ **Dashboard** - Complete analytics overview in one call

### Architecture

The analytics system uses:
- **Materialized Views** - Pre-computed aggregations for fast queries
- **Regular Views** - Real-time data for current statistics
- **Indexes** - Optimized for common query patterns

---

## Database Views

### Materialized Views (Pre-computed)

#### 1. `user_exercise_progress_weekly`
Tracks weekly progress for each user-exercise combination.

**Columns:**
- `user_id`, `exercise_id`, `exercise_name`, `muscle_group`
- `week_start` (date)
- `workout_count`, `max_weight`, `total_reps`, `total_sets`, `total_volume`

**Refresh:** Call `/api/analytics/refresh-views` (admin only)

#### 2. `workout_volume_by_week`
Weekly aggregated workout statistics per user.

**Columns:**
- `user_id`, `week_start`
- `workout_count`, `total_duration_minutes`, `avg_workout_duration`
- `total_volume`, `unique_exercises`

#### 3. `workout_volume_by_month`
Monthly aggregated workout statistics per user.

**Columns:** Same as weekly, but aggregated by month

#### 4. `personal_records`
Maximum weight achieved for each user-exercise combination.

**Columns:**
- `user_id`, `exercise_id`, `exercise_name`, `muscle_group`
- `max_weight`, `reps_at_max`, `achieved_date`, `days_ago`

### Regular Views (Real-time)

#### 5. `muscle_group_distribution`
Distribution of training volume across muscle groups.

#### 6. `user_workout_summary`
Overall workout statistics summary per user.

#### 7. `exercise_frequency`
How often each exercise is performed by each user.

---

## API Endpoints

All analytics endpoints require authentication. Endpoints are under `/api/analytics`.

### 1. Get Progress Summary

**GET** `/api/analytics/progress/summary`

Get overall progress summary for the authenticated user.

**Response (200 OK):**
```json
{
  "user_id": 1,
  "total_workouts": 45,
  "total_exercises": 12,
  "total_workout_minutes": 3375,
  "avg_workout_duration": 75.0,
  "total_volume": 125600.5,
  "exercises_by_muscle_group": {
    "Chest": 3,
    "Back": 4,
    "Legs": 3,
    "Shoulders": 2
  },
  "most_frequent_exercise": "Bench Press",
  "recent_activity_days": 2
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/api/analytics/progress/summary" \
  -H "Authorization: Bearer $TOKEN"
```

---

### 2. Get Exercise Progress

**GET** `/api/analytics/progress/exercise/{exercise_id}`

Track progress for a specific exercise over time.

**Query Parameters:**
- `days` (int, default=90): Number of days to look back (7-365)

**Response (200 OK):**
```json
{
  "exercise_id": 1,
  "exercise_name": "Bench Press",
  "muscle_group": "Chest",
  "data_points": [
    {
      "workout_date": "2025-10-01",
      "max_weight": 80.0,
      "total_reps": 30,
      "total_sets": 3,
      "volume": 2400.0
    },
    {
      "workout_date": "2025-10-08",
      "max_weight": 82.5,
      "total_reps": 30,
      "total_sets": 3,
      "volume": 2475.0
    }
  ],
  "first_workout": "2025-10-01",
  "last_workout": "2025-12-15",
  "total_workouts": 11,
  "starting_weight": 80.0,
  "current_weight": 90.0,
  "weight_gain": 10.0,
  "weight_gain_percentage": 12.5
}
```

**Example:**
```bash
# Last 90 days (default)
curl -X GET "http://localhost:8000/api/analytics/progress/exercise/1" \
  -H "Authorization: Bearer $TOKEN"

# Last 30 days
curl -X GET "http://localhost:8000/api/analytics/progress/exercise/1?days=30" \
  -H "Authorization: Bearer $TOKEN"
```

---

### 3. Get Weekly Volume

**GET** `/api/analytics/volume/weekly`

Get workout volume aggregated by week.

**Query Parameters:**
- `weeks` (int, default=12): Number of weeks to retrieve (1-52)

**Response (200 OK):**
```json
[
  {
    "week_start": "2025-11-25",
    "workout_count": 4,
    "total_duration_minutes": 280,
    "total_volume": 12500.0,
    "unique_exercises": 8,
    "avg_workout_duration": 70.0
  },
  {
    "week_start": "2025-12-02",
    "workout_count": 3,
    "total_duration_minutes": 225,
    "total_volume": 11200.0,
    "unique_exercises": 7,
    "avg_workout_duration": 75.0
  }
]
```

**Example:**
```bash
# Last 12 weeks (default)
curl -X GET "http://localhost:8000/api/analytics/volume/weekly" \
  -H "Authorization: Bearer $TOKEN"

# Last 4 weeks
curl -X GET "http://localhost:8000/api/analytics/volume/weekly?weeks=4" \
  -H "Authorization: Bearer $TOKEN"
```

---

### 4. Get Monthly Volume

**GET** `/api/analytics/volume/monthly`

Get workout volume aggregated by month.

**Query Parameters:**
- `months` (int, default=6): Number of months to retrieve (1-24)

**Response:** Similar format to weekly volume, but by month

**Example:**
```bash
curl -X GET "http://localhost:8000/api/analytics/volume/monthly?months=6" \
  -H "Authorization: Bearer $TOKEN"
```

---

### 5. Get Personal Records

**GET** `/api/analytics/records`

Get personal records (maximum weights) for each exercise.

**Query Parameters:**
- `limit` (int, default=10): Maximum number of PRs to return (1-100)

**Response (200 OK):**
```json
[
  {
    "exercise_id": 1,
    "exercise_name": "Bench Press",
    "muscle_group": "Chest",
    "max_weight": 100.0,
    "reps_at_max": 5,
    "achieved_date": "2025-12-10",
    "days_ago": 5
  },
  {
    "exercise_id": 2,
    "exercise_name": "Squat",
    "muscle_group": "Legs",
    "max_weight": 150.0,
    "reps_at_max": 5,
    "achieved_date": "2025-12-08",
    "days_ago": 7
  }
]
```

**Example:**
```bash
# Get top 10 PRs
curl -X GET "http://localhost:8000/api/analytics/records" \
  -H "Authorization: Bearer $TOKEN"

# Get all PRs
curl -X GET "http://localhost:8000/api/analytics/records?limit=100" \
  -H "Authorization: Bearer $TOKEN"
```

---

### 6. Get Muscle Group Distribution

**GET** `/api/analytics/muscle-groups`

Get distribution of training volume across muscle groups.

**Response (200 OK):**
```json
[
  {
    "muscle_group": "Chest",
    "exercise_count": 3,
    "total_sets": 120,
    "total_volume": 28500.0,
    "percentage": 32.5
  },
  {
    "muscle_group": "Back",
    "exercise_count": 4,
    "total_sets": 140,
    "total_volume": 31200.0,
    "percentage": 35.6
  },
  {
    "muscle_group": "Legs",
    "exercise_count": 3,
    "total_sets": 90,
    "total_volume": 22100.0,
    "percentage": 25.2
  },
  {
    "muscle_group": "Shoulders",
    "exercise_count": 2,
    "total_sets": 60,
    "total_volume": 5900.0,
    "percentage": 6.7
  }
]
```

**Example:**
```bash
curl -X GET "http://localhost:8000/api/analytics/muscle-groups" \
  -H "Authorization: Bearer $TOKEN"
```

---

### 7. Get User Insights

**GET** `/api/analytics/insights`

Get AI-generated insights and recommendations.

**Response (200 OK):**
```json
{
  "user_id": 1,
  "insights": [
    {
      "type": "achievement",
      "title": "New PR: Bench Press!",
      "description": "You hit a new personal record of 100.0kg on Bench Press!",
      "date": "2025-12-10",
      "priority": 5
    },
    {
      "type": "suggestion",
      "title": "Balance Your Shoulders Training",
      "description": "Only 6.7% of your volume goes to Shoulders. Consider adding more exercises!",
      "priority": 2
    },
    {
      "type": "warning",
      "title": "Stay Consistent",
      "description": "You haven't worked out in 3 days. Try to maintain your routine!",
      "priority": 3
    }
  ],
  "generated_at": "2025-12-15T23:00:00Z"
}
```

**Insight Types:**
- `achievement` - New PRs, milestones
- `warning` - Inactivity alerts
- `suggestion` - Training recommendations
- `milestone` - Special achievements (50/100 workouts, etc.)

**Example:**
```bash
curl -X GET "http://localhost:8000/api/analytics/insights" \
  -H "Authorization: Bearer $TOKEN"
```

---

### 8. Get Analytics Dashboard

**GET** `/api/analytics/dashboard`

Get complete analytics dashboard in a single response.

**Response (200 OK):**
```json
{
  "user_id": 1,
  "progress_summary": { ... },
  "workout_streak": {
    "current_streak": 1,
    "longest_streak": 0,
    "total_workout_days": 45,
    "avg_workouts_per_week": 0.0,
    "consistency_score": 0.0
  },
  "recent_volume_by_week": [ ... ],
  "recent_personal_records": [ ... ],
  "muscle_group_distribution": [ ... ],
  "insights": [ ... ],
  "generated_at": "2025-12-15T23:00:00Z"
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/api/analytics/dashboard" \
  -H "Authorization: Bearer $TOKEN"
```

---

### 9. Refresh Analytics Views (Admin Only)

**POST** `/api/analytics/refresh-views`

Refresh all materialized views. Requires superuser authentication.

**Response (204 No Content)**

**Example:**
```bash
curl -X POST "http://localhost:8000/api/analytics/refresh-views" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Note:** This should be automated via cron job (e.g., daily at midnight).

---

## Use Cases & Examples

### Use Case 1: Track Bench Press Progress

```python
import requests

BASE_URL = "http://localhost:8000/api"
headers = {"Authorization": f"Bearer {token}"}

# Get 6-month bench press progress (assuming exercise_id=1)
progress = requests.get(
    f"{BASE_URL}/analytics/progress/exercise/1",
    params={"days": 180},
    headers=headers
).json()

print(f"Exercise: {progress['exercise_name']}")
print(f"Starting weight: {progress['starting_weight']}kg")
print(f"Current weight: {progress['current_weight']}kg")
print(f"Gain: +{progress['weight_gain']}kg ({progress['weight_gain_percentage']}%)")

# Plot progress
import matplotlib.pyplot as plt

dates = [point['workout_date'] for point in progress['data_points']]
weights = [point['max_weight'] for point in progress['data_points']]

plt.plot(dates, weights)
plt.xlabel('Date')
plt.ylabel('Weight (kg)')
plt.title(f"{progress['exercise_name']} Progress")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
```

### Use Case 2: Monitor Training Volume

```python
# Get last 12 weeks of volume data
volume = requests.get(
    f"{BASE_URL}/analytics/volume/weekly",
    params={"weeks": 12},
    headers=headers
).json()

# Calculate average weekly volume
avg_volume = sum(week['total_volume'] for week in volume) / len(volume)
print(f"Average weekly volume: {avg_volume:.2f}kg")

# Check for overtraining (volume dropped significantly)
if len(volume) >= 2:
    recent_volume = volume[-1]['total_volume']
    prev_volume = volume[-2]['total_volume']
    change = ((recent_volume - prev_volume) / prev_volume) * 100

    if change < -20:
        print(f"Warning: Volume dropped {abs(change):.1f}% last week!")
```

### Use Case 3: Identify Muscle Imbalances

```python
# Get muscle group distribution
distribution = requests.get(
    f"{BASE_URL}/analytics/muscle-groups",
    headers=headers
).json()

print("Muscle Group Distribution:")
for muscle in distribution:
    print(f"  {muscle['muscle_group']}: {muscle['percentage']}% ({muscle['total_volume']:.0f}kg)")

# Find neglected muscle groups
threshold = 15.0  # Less than 15% is considered low
neglected = [m for m in distribution if m['percentage'] < threshold]

if neglected:
    print("\nNeglected muscle groups:")
    for muscle in neglected:
        print(f"  - {muscle['muscle_group']} ({muscle['percentage']}%)")
```

### Use Case 4: Dashboard Widget

```python
# Get complete dashboard
dashboard = requests.get(
    f"{BASE_URL}/analytics/dashboard",
    headers=headers
).json()

# Display summary
summary = dashboard['progress_summary']
print(f"Total Workouts: {summary['total_workouts']}")
print(f"Total Volume: {summary['total_volume']:.0f}kg")
print(f"Days Since Last Workout: {summary['recent_activity_days']}")

# Display recent PRs
print("\nRecent Personal Records:")
for pr in dashboard['recent_personal_records'][:3]:
    print(f"  {pr['exercise_name']}: {pr['max_weight']}kg ({pr['days_ago']} days ago)")

# Display insights
print("\nInsights:")
for insight in dashboard['insights'][:3]:
    print(f"  [{insight['type'].upper()}] {insight['title']}")
    print(f"    {insight['description']}")
```

---

## Maintenance

### Refreshing Materialized Views

Materialized views should be refreshed periodically to include new workout data.

#### Option 1: Manual Refresh (Admin)
```bash
curl -X POST "http://localhost:8000/api/analytics/refresh-views" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

#### Option 2: Automated Cron Job
```bash
# Add to crontab: Refresh daily at 2 AM
0 2 * * * curl -X POST http://localhost:8000/api/analytics/refresh-views \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

#### Option 3: Python Script
```python
import requests
import schedule
import time

def refresh_views():
    response = requests.post(
        "http://localhost:8000/api/analytics/refresh-views",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    if response.status_code == 204:
        print("Analytics views refreshed successfully")
    else:
        print(f"Failed to refresh views: {response.status_code}")

# Schedule daily at 2 AM
schedule.every().day.at("02:00").do(refresh_views)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### Performance Considerations

1. **Materialized View Size** - Grows with user data; monitor disk usage
2. **Refresh Time** - Can take seconds to minutes depending on data volume
3. **Concurrent Refresh** - Uses `CONCURRENTLY` to avoid locking tables
4. **Indexes** - Ensure indexes exist for better query performance

### Monitoring Queries

```sql
-- Check materialized view sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE tablename LIKE '%_by_%' OR tablename = 'personal_records'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check last refresh time (requires pg_stat_statements extension)
SELECT relname, last_analyze, last_autoanalyze
FROM pg_stat_user_tables
WHERE relname IN ('user_exercise_progress_weekly', 'workout_volume_by_week');
```

---

## Best Practices

1. **Refresh Schedule** - Refresh views daily or after bulk data imports
2. **API Usage** - Use dashboard endpoint for overview, specific endpoints for details
3. **Caching** - Cache dashboard results for 5-15 minutes in frontend
4. **Date Ranges** - Use appropriate date ranges (90 days for trends, 7 days for recent)
5. **Error Handling** - Handle 404 for exercises with no data gracefully

---

## Troubleshooting

**Q: No data returned for exercise progress**
- Check if user has logged workouts for that exercise
- Verify exercise_id is correct
- Check date range (may need to increase `days` parameter)

**Q: Slow query performance**
- Refresh materialized views: `POST /api/analytics/refresh-views`
- Check if indexes exist
- Consider reducing date range

**Q: Stale data in analytics**
- Materialized views need refreshing
- Call refresh endpoint or wait for scheduled refresh

---

## Future Enhancements

- Advanced streak calculation (consecutive workout days)
- Predicted PRs based on trends
- Exercise recommendations based on goals
- Comparison with similar users (leaderboards)
- Export analytics to PDF/CSV
- Custom date range selection
- Real-time progress notifications
