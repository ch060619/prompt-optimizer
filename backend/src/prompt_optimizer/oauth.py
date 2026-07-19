from __future__ import annotations

import base64
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import token_urlsafe
from threading import Lock
from typing import Protocol
from urllib.parse import urlencode, urlparse

from prompt_optimizer.secrets import SecretStore, new_secret_reference

# RC ID: RC-182. Keep OAuth opt-in, policy-gated, PKCE-protected, and keychain-backed.


class OAuthError(RuntimeError):
    """Base error for the deliberately narrow official OAuth boundary."""


class OAuthNotAllowedError(OAuthError):
    """Raised when a Provider has no confirmed third-party OAuth approval."""


class OAuthCallbackError(OAuthError):
    """Raised when a callback cannot be tied to a live authorization request."""


class OAuthTokenError(OAuthError):
    """Raised when a Provider returns an invalid token response."""


@dataclass(frozen=True)
class OAuthProviderPolicy:
    provider: str
    client_id: str
    authorization_endpoint: str
    token_endpoint: str
    revoke_endpoint: str | None
    scopes: tuple[str, ...]
    official_policy_url: str
    third_party_client_allowed: bool

    @property
    def approved(self) -> bool:
        return bool(
            self.third_party_client_allowed
            and self.official_policy_url
            and self.client_id
            and self.authorization_endpoint
            and self.token_endpoint
        )


# No default Provider is listed until its current third-party client policy is
# explicitly confirmed. Tests and a downstream distribution may inject records.
APPROVED_OAUTH_POLICIES: dict[str, OAuthProviderPolicy] = {}


class OAuthPolicyRegistry:
    def __init__(self, policies: Mapping[str, OAuthProviderPolicy] | None = None) -> None:
        self._policies = dict(policies or APPROVED_OAUTH_POLICIES)

    def approved_providers(self) -> tuple[str, ...]:
        return tuple(sorted(name for name, policy in self._policies.items() if policy.approved))

    def require(self, provider: str) -> OAuthProviderPolicy:
        policy = self._policies.get(provider)
        if policy is None or not policy.approved:
            raise OAuthNotAllowedError(
                f"OAuth is unavailable for {provider}; confirmed third-party approval is required."
            )
        return policy


@dataclass(frozen=True)
class OAuthAuthorization:
    provider: str
    state: str
    authorization_url: str
    redirect_uri: str


@dataclass(frozen=True)
class OAuthCredential:
    provider: str
    access_token_ref: str
    refresh_token_ref: str | None
    expires_at: datetime
    token_type: str

    def is_expired(self, *, now: datetime | None = None) -> bool:
        current = now or datetime.now(UTC)
        return current >= self.expires_at


class OAuthTransport(Protocol):
    def exchange_code(
        self,
        policy: OAuthProviderPolicy,
        *,
        code: str,
        code_verifier: str,
        redirect_uri: str,
    ) -> Mapping[str, object]:
        ...

    def refresh_token(
        self,
        policy: OAuthProviderPolicy,
        *,
        refresh_token: str,
    ) -> Mapping[str, object]:
        ...

    def revoke_token(
        self,
        policy: OAuthProviderPolicy,
        *,
        token: str,
    ) -> None:
        ...


@dataclass(frozen=True)
class _PendingAuthorization:
    provider: str
    state: str
    code_verifier: str
    redirect_uri: str
    created_at: datetime


class OAuthClient:
    def __init__(
        self,
        *,
        policies: OAuthPolicyRegistry | None = None,
        secret_store: SecretStore,
        transport: OAuthTransport,
        now: Callable[[], datetime] | None = None,
        max_authorization_age: timedelta = timedelta(minutes=10),
        browser_opener: Callable[[str], None] | None = None,
    ) -> None:
        self.policies = policies or OAuthPolicyRegistry()
        self.secret_store = secret_store
        self.transport = transport
        self._now = now or (lambda: datetime.now(UTC))
        self._max_authorization_age = max_authorization_age
        self._browser_opener = browser_opener
        self._pending: dict[str, _PendingAuthorization] = {}
        self._open_callbacks: set[str] = set()
        self._lock = Lock()

    def start(self, provider: str, *, redirect_uri: str) -> OAuthAuthorization:
        policy = self.policies.require(provider)
        _validate_loopback_redirect(redirect_uri)
        state = token_urlsafe(32)
        verifier = token_urlsafe(64)
        challenge = _code_challenge(verifier)
        authorization_url = f"{policy.authorization_endpoint}?{urlencode({
            'response_type': 'code',
            'client_id': policy.client_id,
            'redirect_uri': redirect_uri,
            'scope': ' '.join(policy.scopes),
            'state': state,
            'code_challenge': challenge,
            'code_challenge_method': 'S256',
        })}"
        with self._lock:
            self._pending[state] = _PendingAuthorization(
                provider=provider,
                state=state,
                code_verifier=verifier,
                redirect_uri=redirect_uri,
                created_at=self._now(),
            )
            self._open_callbacks.add(redirect_uri)
        if self._browser_opener is not None:
            self._browser_opener(authorization_url)
        return OAuthAuthorization(provider, state, authorization_url, redirect_uri)

    def callback_open(self, redirect_uri: str) -> bool:
        with self._lock:
            return redirect_uri in self._open_callbacks

    def complete(
        self,
        authorization: OAuthAuthorization,
        *,
        code: str,
        state: str,
        redirect_uri: str,
    ) -> OAuthCredential:
        if not code:
            raise OAuthCallbackError("OAuth callback did not contain a code.")
        with self._lock:
            pending = self._pending.pop(state, None)
            if pending is not None:
                self._open_callbacks.discard(pending.redirect_uri)
        if pending is None or state != authorization.state:
            raise OAuthCallbackError("OAuth state is invalid or has already been used.")
        if pending.provider != authorization.provider or pending.redirect_uri != redirect_uri:
            raise OAuthCallbackError(
                "OAuth callback redirect does not match the authorization request."
            )
        if self._now() - pending.created_at > self._max_authorization_age:
            raise OAuthCallbackError("OAuth authorization request expired.")
        policy = self.policies.require(pending.provider)
        payload = self.transport.exchange_code(
            policy,
            code=code,
            code_verifier=pending.code_verifier,
            redirect_uri=redirect_uri,
        )
        return self._store_token_payload(pending.provider, payload)

    def cancel(self, authorization: OAuthAuthorization) -> None:
        with self._lock:
            pending = self._pending.pop(authorization.state, None)
            if pending is not None:
                self._open_callbacks.discard(pending.redirect_uri)

    def refresh(self, credential: OAuthCredential) -> OAuthCredential:
        if credential.refresh_token_ref is None:
            raise OAuthTokenError("OAuth credential has no refresh token.")
        refresh_token = self.secret_store.get(credential.refresh_token_ref)
        if refresh_token is None:
            raise OAuthTokenError("OAuth refresh token reference is missing.")
        payload = self.transport.refresh_token(
            self.policies.require(credential.provider),
            refresh_token=refresh_token,
        )
        refreshed = self._store_token_payload(credential.provider, payload)
        self.secret_store.delete(credential.access_token_ref)
        self.secret_store.delete(credential.refresh_token_ref)
        return refreshed

    def revoke(self, credential: OAuthCredential) -> None:
        token_ref = credential.refresh_token_ref or credential.access_token_ref
        token = self.secret_store.get(token_ref)
        try:
            if token is not None and self.policies.require(credential.provider).revoke_endpoint:
                self.transport.revoke_token(
                    self.policies.require(credential.provider),
                    token=token,
                )
        finally:
            self.secret_store.delete(credential.access_token_ref)
            if credential.refresh_token_ref is not None:
                self.secret_store.delete(credential.refresh_token_ref)

    def _store_token_payload(
        self,
        provider: str,
        payload: Mapping[str, object],
    ) -> OAuthCredential:
        access_token = _required_token(payload, "access_token")
        refresh_token = payload.get("refresh_token")
        if refresh_token is not None and not isinstance(refresh_token, str):
            raise OAuthTokenError("OAuth refresh token response is invalid.")
        raw_expires_in = payload.get("expires_in", 3600)
        if isinstance(raw_expires_in, bool) or not isinstance(raw_expires_in, (str, int, float)):
            raise OAuthTokenError("OAuth token expiry is invalid.")
        try:
            expires_in = int(raw_expires_in)
        except (TypeError, ValueError) as exc:
            raise OAuthTokenError("OAuth token expiry is invalid.") from exc
        if expires_in <= 0:
            raise OAuthTokenError("OAuth token expiry must be positive.")
        access_ref = new_secret_reference()
        refresh_ref = new_secret_reference() if refresh_token else None
        self.secret_store.put(access_ref, access_token)
        try:
            if refresh_ref is not None and isinstance(refresh_token, str):
                self.secret_store.put(refresh_ref, refresh_token)
        except Exception:
            self.secret_store.delete(access_ref)
            raise
        token_type = payload.get("token_type", "Bearer")
        if not isinstance(token_type, str) or not token_type:
            token_type = "Bearer"
        return OAuthCredential(
            provider=provider,
            access_token_ref=access_ref,
            refresh_token_ref=refresh_ref,
            expires_at=self._now() + timedelta(seconds=expires_in),
            token_type=token_type,
        )


def _required_token(payload: Mapping[str, object], name: str) -> str:
    value = payload.get(name)
    if not isinstance(value, str) or not value:
        raise OAuthTokenError(f"OAuth token response has no valid {name}.")
    return value


def _code_challenge(verifier: str) -> str:
    return base64.urlsafe_b64encode(sha256(verifier.encode()).digest()).rstrip(b"=").decode()


def _validate_loopback_redirect(redirect_uri: str) -> None:
    parsed = urlparse(redirect_uri)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}
        or parsed.port is None
        or not (1024 <= parsed.port <= 65535)
    ):
        raise OAuthCallbackError("OAuth redirect must use an ephemeral loopback HTTP port.")
