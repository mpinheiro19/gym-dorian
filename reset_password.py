"""Script to reset user password"""
from app.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

def reset_password(email: str, new_password: str):
    """Reset password for a user"""
    db = SessionLocal()

    try:
        # Find user
        user = db.query(User).filter(User.email == email).first()

        if not user:
            print(f"❌ User not found: {email}")
            return

        # Update password
        user.password_hash = get_password_hash(new_password)
        db.commit()

        print(f"✅ Password reset successfully!")
        print(f"   Email: {email}")
        print(f"   New Password: {new_password}")
        print(f"\n📝 You can now login with:")
        print(f"   Email: {email}")
        print(f"   Password: {new_password}")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Reset password for test user
    reset_password("test@example.com", "test123")

    # Also reset for other common test users
    print("\n" + "="*60 + "\n")
    reset_password("admin@gym.com", "admin123")
