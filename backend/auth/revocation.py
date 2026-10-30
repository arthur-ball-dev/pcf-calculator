"""
Token revocation (issue #24).

The denylist is a database table because the deployment has no Redis. Expired
rows are purged whenever a token is revoked, so the table's size follows the
number of logouts in the last token lifetime and needs no scheduled job.
"""

from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from backend.auth.jwt import InvalidTokenError, decode_token
from backend.models.revoked_token import RevokedToken


def is_token_revoked(db: Session, jti: str) -> bool:
    """Return True if this token ID is on the denylist."""
    return db.get(RevokedToken, jti) is not None


def revoke_token(db: Session, payload: Dict[str, Any]) -> None:
    """
    Add a decoded token to the denylist, and purge rows that have expired.

    Revoking the same token twice, for instance from two concurrent logouts,
    is not an error.
    """
    expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    db.execute(
        insert(RevokedToken)
        .values(jti=payload["jti"], expires_at=expires_at)
        .on_conflict_do_nothing(index_elements=["jti"])
    )
    db.execute(delete(RevokedToken).where(RevokedToken.expires_at < datetime.now(timezone.utc)))
    db.commit()


def decode_active_token(token: str, db: Session) -> Dict[str, Any]:
    """
    Decode a token and require that it can still be used.

    A token without a jti could never be revoked, so it is rejected. Every path
    that authenticates a request goes through here rather than decode_token.

    Raises:
        TokenExpiredError: If the token has expired
        InvalidTokenError: If the token is invalid, has no jti, or was revoked
    """
    payload = decode_token(token)
    jti = payload.get("jti")
    if not jti or is_token_revoked(db, jti):
        raise InvalidTokenError("Token has been revoked")
    return payload
