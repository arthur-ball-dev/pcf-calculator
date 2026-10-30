"""
Token revocation and logout (issue #24).

A token must stop working the moment its owner logs out, on every path that
reads a token, not only when it expires an hour later.
"""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from backend.auth.dependencies import get_current_user_from_token, get_optional_user
from backend.auth.jwt import create_access_token, decode_token
from backend.auth.revocation import is_token_revoked, revoke_token
from backend.models import RevokedToken

LOGOUT = "/api/v1/auth/logout"
ME = "/api/v1/auth/me"
REFRESH = "/api/v1/auth/refresh"


def _claims(user):
    return {"user_id": user.id, "username": user.username, "role": user.role}


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def user(test_user_factory):
    return test_user_factory(username="revocation_user", email="revocation@example.com")


@pytest.fixture
def token(user):
    return create_access_token(_claims(user))


class TestJtiClaim:
    def test_tokens_carry_a_jti(self, token):
        assert decode_token(token)["jti"]

    def test_two_tokens_for_one_user_have_different_jtis(self, user):
        first = decode_token(create_access_token(_claims(user)))
        second = decode_token(create_access_token(_claims(user)))
        assert first["jti"] != second["jti"]


class TestLogout:
    def test_logout_returns_204(self, client, token):
        assert client.post(LOGOUT, headers=_headers(token)).status_code == 204

    def test_logged_out_token_is_rejected(self, client, token):
        assert client.get(ME, headers=_headers(token)).status_code == 200

        client.post(LOGOUT, headers=_headers(token))

        assert client.get(ME, headers=_headers(token)).status_code == 401

    def test_logged_out_token_cannot_be_refreshed(self, client, token):
        client.post(LOGOUT, headers=_headers(token))

        assert client.post(REFRESH, headers=_headers(token)).status_code == 401

    def test_logout_twice_returns_401(self, client, token):
        client.post(LOGOUT, headers=_headers(token))

        assert client.post(LOGOUT, headers=_headers(token)).status_code == 401

    def test_logout_without_token_returns_401(self, client):
        assert client.post(LOGOUT).status_code == 401

    def test_other_tokens_of_the_same_user_keep_working(self, client, user, token):
        other = create_access_token(_claims(user))

        client.post(LOGOUT, headers=_headers(token))

        assert client.get(ME, headers=_headers(other)).status_code == 200


class TestRefreshRotation:
    def test_refresh_revokes_the_presented_token(self, client, token):
        assert client.post(REFRESH, headers=_headers(token)).status_code == 200

        assert client.get(ME, headers=_headers(token)).status_code == 401

    def test_refreshed_token_works(self, client, token):
        fresh = client.post(REFRESH, headers=_headers(token)).json()["access_token"]

        assert client.get(ME, headers=_headers(fresh)).status_code == 200

    def test_a_token_can_only_be_refreshed_once(self, client, token):
        client.post(REFRESH, headers=_headers(token))

        assert client.post(REFRESH, headers=_headers(token)).status_code == 401

    def test_logout_ends_a_refreshed_session(self, client, token):
        fresh = client.post(REFRESH, headers=_headers(token)).json()["access_token"]

        client.post(LOGOUT, headers=_headers(fresh))

        assert client.get(ME, headers=_headers(token)).status_code == 401
        assert client.get(ME, headers=_headers(fresh)).status_code == 401


class TestEveryTokenPathChecksRevocation:
    def test_get_current_user_from_token(self, db_session, token):
        revoke_token(db_session, decode_token(token))

        with pytest.raises(HTTPException) as exc_info:
            get_current_user_from_token(token, db_session)
        assert exc_info.value.status_code == 401

    def test_optional_user_is_anonymous_with_a_revoked_token(self, db_session, token):
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        assert get_optional_user(credentials, db_session) is not None

        revoke_token(db_session, decode_token(token))

        assert get_optional_user(credentials, db_session) is None

    def test_token_without_jti_is_rejected(self, client, user):
        from backend.auth import jwt as jwt_module
        import jwt as pyjwt

        payload = decode_token(create_access_token(_claims(user)))
        del payload["jti"]
        unrevocable = pyjwt.encode(
            payload, jwt_module.JWT_SECRET_KEY, algorithm=jwt_module.JWT_ALGORITHM
        )

        assert client.get(ME, headers=_headers(unrevocable)).status_code == 401


class TestDenylistStorage:
    def test_row_expires_with_the_token(self, db_session, token):
        payload = decode_token(token)

        revoke_token(db_session, payload)

        row = db_session.get(RevokedToken, payload["jti"])
        assert int(row.expires_at.timestamp()) == payload["exp"]

    def test_revoking_twice_is_harmless(self, db_session, token):
        payload = decode_token(token)

        revoke_token(db_session, payload)
        revoke_token(db_session, payload)

        assert is_token_revoked(db_session, payload["jti"])

    def test_revoking_purges_expired_rows(self, db_session, token):
        expired = RevokedToken(
            jti="a" * 32,
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        )
        still_valid = RevokedToken(
            jti="b" * 32,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        )
        db_session.add_all([expired, still_valid])
        db_session.commit()

        revoke_token(db_session, decode_token(token))

        assert db_session.get(RevokedToken, "a" * 32) is None
        assert db_session.get(RevokedToken, "b" * 32) is not None
