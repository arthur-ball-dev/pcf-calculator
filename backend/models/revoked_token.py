"""
Revoked access tokens (issue #24).

A row exists only while the token would otherwise still be valid: once
expires_at has passed, signature validation rejects the token by itself and
the row can be purged.
"""

from sqlalchemy import Column, DateTime, Index, String

from backend.models.base import Base


class RevokedToken(Base):
    __tablename__ = "revoked_tokens"

    jti = Column(String(32), primary_key=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (Index("idx_revoked_tokens_expires_at", "expires_at"),)
