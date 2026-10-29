"""
User Model for Authentication

TASK-BE-P7-018: JWT Authentication + Role-Based Admin Access

This module defines the User model for authentication and authorization.

Roles:
- user: Can read products, calculations, emission factors
- admin: All user permissions + create/update/delete emission factors + data sync

References:
- SPEC: TASK-BE-P7-018 User Model Schema
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Index,
)
from sqlalchemy.sql import func

from backend.models.base import Base, generate_uuid


class User(Base):
    """
    User model for authentication and authorization.

    Supports role-based access control (RBAC) with two roles:
    - user: Standard user with read access
    - admin: Administrator with full access

    Attributes:
        id: Primary key (UUID hex string)
        username: Unique username for login
        email: Unique email address
        hashed_password: bcrypt-hashed password
        role: User role (user or admin)
        is_active: Account active status
        created_at: Account creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "users"

    # Primary key - UUID hex string
    id = Column(
        String(32),
        primary_key=True,
        default=generate_uuid
    )

    # Login credentials
    username = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    email = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    # Password stored as bcrypt hash
    hashed_password = Column(
        String(255),
        nullable=False
    )

    # Role-based access control
    # Values: "user" (default), "admin"
    role = Column(
        String(20),
        nullable=False,
        default="user"
    )

    # Account status
    is_active = Column(
        Boolean,
        nullable=False,
        default=True
    )

    # Audit timestamps
    created_at = Column(
        DateTime,
        nullable=False,
        default=func.now()
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        default=func.now(),
        onupdate=func.now()
    )

    # Table indexes
    __table_args__ = (
        Index('idx_users_username', 'username'),
        Index('idx_users_email', 'email'),
        Index('idx_users_role', 'role'),
        Index('idx_users_active', 'is_active'),
    )

    def __repr__(self) -> str:
        return f"<User(username='{self.username}', role='{self.role}')>"

    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == "admin"


__all__ = ['User']
