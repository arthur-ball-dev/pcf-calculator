"""
Seed data for E2E test user.

TASK-QA-P7-032: E2E Test Authentication Integration

This module creates a test user for E2E (Playwright) tests.
The user credentials match those expected by the auth fixture.

Test User Credentials:
- Username: e2e-test
- Email: e2e-test@example.com
- Password: E2ETestPassword123!
- Role: user
- Active: True

Usage:
    from backend.database.seeds.e2e_test_user import seed_e2e_test_user
    from backend.database.connection import db_context

    with db_context() as session:
        seed_e2e_test_user(session)

Or via command line:
    cd backend && python -c "from backend.database.seeds.e2e_test_user import seed_e2e_test_user_standalone; seed_e2e_test_user_standalone()"
"""

from typing import Optional
from sqlalchemy.orm import Session

from backend.auth.password import hash_password


# E2E Test User Configuration
# Must match credentials in frontend/tests/e2e/fixtures/auth.fixture.ts
E2E_TEST_USER = {
    "username": "e2e-test",
    "email": "e2e-test@example.com",
    "password": "E2ETestPassword123!",
    "role": "user",
    "is_active": True,
}


def seed_e2e_test_user(session: Session, force_update: bool = False) -> Optional[str]:
    """
    Seed the E2E test user in the database.

    Creates a user with credentials expected by the E2E auth fixture.
    If user already exists:
      - force_update=False (default): Skip and return existing user ID
      - force_update=True: Update password hash and return user ID

    Args:
        session: SQLAlchemy database session
        force_update: If True, update existing user's password

    Returns:
        User ID if created/updated, None if skipped

    Example:
        from backend.database.connection import db_context
        from backend.database.seeds.e2e_test_user import seed_e2e_test_user

        with db_context() as session:
            user_id = seed_e2e_test_user(session)
            print(f"E2E test user ready: {user_id}")
    """
    from backend.models.user import User

    # Check if user already exists by username
    existing_user = session.query(User).filter(
        User.username == E2E_TEST_USER["username"]
    ).first()

    if existing_user:
        if force_update:
            # Update password hash
            existing_user.hashed_password = hash_password(E2E_TEST_USER["password"])
            existing_user.is_active = E2E_TEST_USER["is_active"]
            session.commit()
            return existing_user.id
        else:
            # User exists, skip creation
            return existing_user.id

    # Create new user
    user = User(
        username=E2E_TEST_USER["username"],
        email=E2E_TEST_USER["email"],
        hashed_password=hash_password(E2E_TEST_USER["password"]),
        role=E2E_TEST_USER["role"],
        is_active=E2E_TEST_USER["is_active"],
    )

    session.add(user)
    session.commit()
    session.refresh(user)

    return user.id


def verify_e2e_test_user(session: Session) -> bool:
    """
    Verify that the E2E test user exists and is active.

    Args:
        session: SQLAlchemy database session

    Returns:
        True if user exists and is active, False otherwise

    Example:
        from backend.database.connection import db_context
        from backend.database.seeds.e2e_test_user import verify_e2e_test_user

        with db_context() as session:
            if verify_e2e_test_user(session):
                print("E2E test user is ready")
            else:
                print("E2E test user needs to be seeded")
    """
    from backend.models.user import User

    user = session.query(User).filter(
        User.username == E2E_TEST_USER["username"]
    ).first()

    return user is not None and user.is_active


def delete_e2e_test_user(session: Session) -> bool:
    """
    Delete the E2E test user from the database.

    Use this for cleanup after E2E test runs if needed.

    Args:
        session: SQLAlchemy database session

    Returns:
        True if user was deleted, False if not found
    """
    from backend.models.user import User

    user = session.query(User).filter(
        User.username == E2E_TEST_USER["username"]
    ).first()

    if user:
        session.delete(user)
        session.commit()
        return True

    return False


def seed_e2e_test_user_standalone():
    """
    Standalone function to seed E2E test user.

    Can be called directly from command line:
        python -c "from backend.database.seeds.e2e_test_user import seed_e2e_test_user_standalone; seed_e2e_test_user_standalone()"

    This function handles its own database connection.
    """
    from backend.database.connection import db_context

    with db_context() as session:
        user_id = seed_e2e_test_user(session, force_update=True)
        if user_id:
            print(f"E2E test user seeded successfully")
            print(f"  Username: {E2E_TEST_USER['username']}")
            print(f"  Email: {E2E_TEST_USER['email']}")
            print(f"  User ID: {user_id}")
        else:
            print("Failed to seed E2E test user")


__all__ = [
    'E2E_TEST_USER',
    'seed_e2e_test_user',
    'verify_e2e_test_user',
    'delete_e2e_test_user',
    'seed_e2e_test_user_standalone',
]
