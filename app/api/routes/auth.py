"""Authentication routes for user registration and login."""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.crud.user import create_user, authenticate_user, get_user_by_email
from app.schemas.user_schema import UserCreate, UserResponse, Token
from app.api.dependencies.auth import get_current_active_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.

    Creates a new user with the provided email and password.
    Automatically creates default user settings.

    Args:
        user_in: User registration data (email, password, full_name)
        db: Database session

    Returns:
        UserResponse: Created user information (without password)

    Raises:
        HTTPException 400: If email is already registered
    """
    # Check if user already exists
    existing_user = get_user_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    user = create_user(db, user_in)
    return user


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login with email and password to get JWT access token.

    Uses OAuth2 password flow. The username field should contain the email.

    Args:
        form_data: OAuth2 form with username (email) and password
        db: Database session

    Returns:
        Token: JWT access token and token type

    Raises:
        HTTPException 401: If credentials are invalid
    """
    # Authenticate user (username field contains email)
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/test-token", response_model=UserResponse)
def test_token(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Test access token validity.

    Protected endpoint that requires valid JWT token.
    Useful for testing authentication.

    Args:
        db: Database session
        current_user: Current authenticated user from token

    Returns:
        UserResponse: Current user information
    """
    return current_user
