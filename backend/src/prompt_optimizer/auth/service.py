from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from prompt_optimizer.core.models import UserPublic

MINIMUM_SECRET_BYTES = 32


class AuthError(RuntimeError):
    pass


class AuthService:
    def __init__(self, secret: str | None = None) -> None:
        configured_secret = secret or os.getenv("PROMPT_OPTIMIZER_JWT_SECRET")
        if configured_secret is None:
            if _is_production():
                raise AuthError(
                    "生产环境必须设置至少 32 字节的 PROMPT_OPTIMIZER_JWT_SECRET。"
                )
            configured_secret = secrets.token_urlsafe(48)
        if _is_production() and len(configured_secret.encode("utf-8")) < MINIMUM_SECRET_BYTES:
            raise AuthError("PROMPT_OPTIMIZER_JWT_SECRET 必须至少为 32 字节。")
        self.secret = configured_secret
        self.password_hasher = PasswordHasher()

    def hash_password(self, password: str) -> str:
        return self.password_hasher.hash(password)

    def verify_password(self, password: str, password_hash: str) -> bool:
        if not password_hash.startswith("$argon2"):
            return self._verify_legacy_password(password, password_hash)
        try:
            return self.password_hasher.verify(password_hash, password)
        except (InvalidHashError, VerificationError):
            return False

    def needs_password_rehash(self, password_hash: str) -> bool:
        return not password_hash.startswith("$argon2") or self.password_hasher.check_needs_rehash(
            password_hash
        )

    def create_token(self, user: UserPublic, expires_delta: timedelta | None = None) -> str:
        expires_at = datetime.now(UTC) + (expires_delta or timedelta(hours=12))
        payload = {
            "sub": str(user.id),
            "username": user.username,
            "exp": int(expires_at.timestamp()),
        }
        return jwt.encode(payload, self.secret, algorithm="HS256")

    def read_token(self, token: str) -> int:
        try:
            payload = jwt.decode(token, self.secret, algorithms=["HS256"])
        except jwt.ExpiredSignatureError as exc:
            raise AuthError("token 已过期。") from exc
        except jwt.InvalidTokenError as exc:
            raise AuthError("无效 token。") from exc
        sub = payload.get("sub")
        if not isinstance(sub, str) or not sub.isdigit():
            raise AuthError("无效 token。")
        return int(sub)

    @staticmethod
    def _verify_legacy_password(password: str, password_hash: str) -> bool:
        try:
            salt, expected = password_hash.split("$", 1)
            digest = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt.encode("utf-8"),
                120_000,
            )
        except ValueError:
            return False
        actual = base64.urlsafe_b64encode(digest).decode("ascii")
        return hmac.compare_digest(actual, expected)


def _is_production() -> bool:
    return os.getenv("PROMPT_OPTIMIZER_ENV", "").lower() == "production"
