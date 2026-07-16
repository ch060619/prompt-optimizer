from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta

from prompt_optimizer.core.models import UserPublic
from prompt_optimizer.identity import compatible_env

# RC ID: RC-054. Prefer Rabbit Code JWT configuration with a legacy fallback.


class AuthError(RuntimeError):
    pass


class AuthService:
    def __init__(self, secret: str | None = None) -> None:
        self.secret = secret or compatible_env("JWT_SECRET") or "dev-secret-change-me"

    def hash_password(self, password: str, salt: str | None = None) -> str:
        current_salt = salt or secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            current_salt.encode("utf-8"),
            120_000,
        )
        return f"{current_salt}${base64.urlsafe_b64encode(digest).decode('ascii')}"

    def verify_password(self, password: str, password_hash: str) -> bool:
        try:
            salt, expected = password_hash.split("$", 1)
        except ValueError:
            return False
        actual = self.hash_password(password, salt).split("$", 1)[1]
        return hmac.compare_digest(actual, expected)

    def create_token(self, user: UserPublic, expires_delta: timedelta | None = None) -> str:
        expires_at = datetime.now(UTC) + (expires_delta or timedelta(hours=12))
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "sub": str(user.id),
            "username": user.username,
            "exp": int(expires_at.timestamp()),
        }
        signing_input = f"{self._encode(header)}.{self._encode(payload)}"
        signature = self._sign(signing_input)
        return f"{signing_input}.{signature}"

    def read_token(self, token: str) -> int:
        parts = token.split(".")
        if len(parts) != 3:
            raise AuthError("无效 token。")
        signing_input = f"{parts[0]}.{parts[1]}"
        if not hmac.compare_digest(self._sign(signing_input), parts[2]):
            raise AuthError("无效 token。")
        payload = self._decode(parts[1])
        exp = payload.get("exp")
        sub = payload.get("sub")
        if not isinstance(exp, int) or exp < int(datetime.now(UTC).timestamp()):
            raise AuthError("token 已过期。")
        if not isinstance(sub, str) or not sub.isdigit():
            raise AuthError("无效 token。")
        return int(sub)

    def _sign(self, value: str) -> str:
        digest = hmac.new(self.secret.encode("utf-8"), value.encode("utf-8"), hashlib.sha256)
        return base64.urlsafe_b64encode(digest.digest()).rstrip(b"=").decode("ascii")

    @classmethod
    def _encode(cls, payload: Mapping[str, object]) -> str:
        data = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

    @staticmethod
    def _decode(value: str) -> dict[str, object]:
        padding = "=" * (-len(value) % 4)
        try:
            payload = json.loads(base64.urlsafe_b64decode(f"{value}{padding}"))
        except (ValueError, json.JSONDecodeError) as exc:
            raise AuthError("无效 token。") from exc
        if not isinstance(payload, dict):
            raise AuthError("无效 token。")
        return payload
