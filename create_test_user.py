"""Script to create a test user for debugging"""
from app.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

def create_test_user():
    """Create a test user"""
    db = SessionLocal()

    try:
        # Check if test user already exists
        test_email = "test@example.com"
        existing = db.query(User).filter(User.email == test_email).first()

        if existing:
            print(f"✅ Test user already exists: {test_email}")
            print(f"   ID: {existing.id}")
            print(f"   Active: {existing.is_active}")
            print(f"   Superuser: {existing.is_superuser}")
            return

        # Create test user
        test_password = "test123"
        hashed_password = get_password_hash(test_password)

        user = User(
            email=test_email,
            password_hash=hashed_password,
            full_name="Test User",
            is_active=True,
            is_superuser=False
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        print("✅ Test user created successfully!")
        print(f"   Email: {test_email}")
        print(f"   Password: {test_password}")
        print(f"   ID: {user.id}")
        print(f"\n📝 Use these credentials to login:")
        print(f"   Email: test@example.com")
        print(f"   Password: test123")

    except Exception as e:
        print(f"❌ Error creating user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()
