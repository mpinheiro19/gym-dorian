"""
Performance and stress tests for the API.

These tests verify that the application can handle load and performs
within acceptable limits. Mark as slow since they take longer to run.
"""

import pytest
import sys
import os
import time
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from tests.fixtures.factories import ExerciseFactory, WorkoutSessionFactory


@pytest.mark.integration
@pytest.mark.slow
class TestDatabasePerformance:
    """Test suite for database query performance."""
    
    def test_bulk_exercise_insert_performance(self, db_session: Session):
        """Test inserting multiple exercises efficiently."""
        start_time = time.time()
        
        # Create 100 exercises
        exercises = ExerciseFactory.create_batch(100)
        db_session.add_all(exercises)
        db_session.commit()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete in reasonable time (adjust threshold as needed)
        assert duration < 2.0, f"Bulk insert took {duration:.2f}s (threshold: 2.0s)"
        
        # Verify all were inserted
        count = db_session.query(ExerciseFactory.create().__class__).count()
        assert count == 100
    
    def test_query_performance_with_large_dataset(self, db_session: Session):
        """Test query performance with larger dataset."""
        from models.exercise import Exercise
        
        # Create 200 exercises
        exercises = ExerciseFactory.create_batch(200)
        db_session.add_all(exercises)
        db_session.commit()
        
        start_time = time.time()
        
        # Perform query
        results = db_session.query(Exercise).filter(
            Exercise.muscle_group == "Group 0"
        ).all()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Query should be fast even with larger dataset
        assert duration < 0.5, f"Query took {duration:.2f}s (threshold: 0.5s)"
        assert len(results) > 0
    
    def test_workout_session_with_many_exercises(self, db_session: Session, sample_exercises):
        """Test creating workout sessions with many exercises."""
        from models.log import WorkoutSession, LogExercise
        from datetime import date
        
        start_time = time.time()
        
        # Create session with 10 exercises
        session = WorkoutSession(date=date.today())
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)
        
        # Add 10 exercise logs
        logs = [
            LogExercise(
                session_id=session.id,
                exercise_id=sample_exercises[i % len(sample_exercises)].id,
                sets_completed=3,
                top_weight=100.0 + i * 10,
                total_reps=30
            )
            for i in range(10)
        ]
        
        db_session.add_all(logs)
        db_session.commit()
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert duration < 1.0, f"Operation took {duration:.2f}s (threshold: 1.0s)"


@pytest.mark.integration
@pytest.mark.slow
class TestAPIEndpointPerformance:
    """Test suite for API endpoint performance."""
    
    def test_health_endpoint_response_time(self, client: TestClient):
        """Test that health check responds quickly."""
        start_time = time.time()
        
        response = client.get("/")
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert response.status_code == 200
        assert duration < 0.1, f"Health check took {duration:.2f}s (threshold: 0.1s)"
    
    def test_multiple_concurrent_requests(self, client: TestClient):
        """Test handling multiple requests in sequence."""
        start_time = time.time()
        
        # Make 50 requests
        for _ in range(50):
            response = client.get("/")
            assert response.status_code == 200
        
        end_time = time.time()
        duration = end_time - start_time
        avg_time = duration / 50
        
        # Average response time should be fast
        assert avg_time < 0.05, f"Average response time: {avg_time:.3f}s (threshold: 0.05s)"


@pytest.mark.integration
@pytest.mark.slow
class TestMemoryAndResourceUsage:
    """Test suite for memory and resource usage."""
    
    def test_memory_cleanup_after_operations(self, db_session: Session):
        """Test that memory is properly cleaned up after operations."""
        import gc
        from models.exercise import Exercise
        
        # Force garbage collection before test
        gc.collect()
        
        # Create and delete many objects
        for i in range(100):
            exercise = Exercise(name=f"Exercise {i}")
            db_session.add(exercise)
            db_session.commit()
            db_session.delete(exercise)
            db_session.commit()
        
        # Force garbage collection
        gc.collect()
        
        # Session should still be functional
        assert db_session.is_active
        
        # Should be able to query
        count = db_session.query(Exercise).count()
        assert count == 0
    
    def test_large_query_result_handling(self, db_session: Session):
        """Test handling large query results efficiently."""
        from models.exercise import Exercise
        
        # Create 500 exercises
        exercises = ExerciseFactory.create_batch(500)
        db_session.add_all(exercises)
        db_session.commit()
        
        start_time = time.time()
        
        # Query all exercises
        results = db_session.query(Exercise).all()
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert len(results) == 500
        assert duration < 1.0, f"Large query took {duration:.2f}s (threshold: 1.0s)"


@pytest.mark.integration
@pytest.mark.slow
class TestConcurrencyAndRaceConditions:
    """Test suite for concurrency issues."""
    
    def test_concurrent_session_creation(self, db_session: Session):
        """
        Test creating multiple sessions doesn't cause conflicts.
        
        Note: This is a simplified test. For true concurrency testing,
        you would need to use threading or async operations.
        """
        from models.log import WorkoutSession
        from datetime import date
        
        sessions = [
            WorkoutSession(user_id=1, date=date.today())
            for _ in range(10)
        ]
        
        # Add all at once
        db_session.add_all(sessions)
        db_session.commit()
        
        # Verify all were created with unique IDs
        db_session.expire_all()
        all_sessions = db_session.query(WorkoutSession).all()
        ids = [s.id for s in all_sessions]
        
        assert len(ids) == len(set(ids)), "Duplicate IDs detected"
        assert len(all_sessions) == 10


@pytest.mark.integration
@pytest.mark.slow
class TestScalability:
    """Test suite for scalability concerns."""
    
    def test_pagination_efficiency(self, db_session: Session):
        """Test that pagination works efficiently with large datasets."""
        from models.exercise import Exercise
        
        # Create 1000 exercises
        exercises = ExerciseFactory.create_batch(1000)
        db_session.add_all(exercises)
        db_session.commit()
        
        # Test paginated queries
        page_size = 50
        start_time = time.time()
        
        # Get first page
        page_1 = db_session.query(Exercise).limit(page_size).all()
        
        # Get second page
        page_2 = db_session.query(Exercise).offset(page_size).limit(page_size).all()
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert len(page_1) == page_size
        assert len(page_2) == page_size
        assert page_1[0].id != page_2[0].id
        assert duration < 0.5, f"Pagination took {duration:.2f}s (threshold: 0.5s)"
    
    def test_complex_join_performance(self, db_session: Session, sample_workout_session):
        """Test performance of queries with joins."""
        from models.log import WorkoutSession, LogExercise
        from models.exercise import Exercise
        
        start_time = time.time()
        
        # Query with joins
        results = db_session.query(WorkoutSession).join(
            LogExercise
        ).join(
            Exercise
        ).filter(
            WorkoutSession.user_id == 1
        ).all()
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert len(results) > 0
        assert duration < 0.5, f"Join query took {duration:.2f}s (threshold: 0.5s)"
