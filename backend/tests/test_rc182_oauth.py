from __future__ import annotations

from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlparse

import pytest

from prompt_optimizer.oauth import (
    OAuthCallbackError,
    OAuthClient,
    OAuthNotAllowedError,
    OAuthPolicyRegistry,
    OAuthProviderPolicy,
)
from prompt_optimizer.secrets import MemorySecretStore

# RC ID: RC-182. Verify policy gating, PKCE/state, callback cleanup, refresh, and revoke.


POLICY = OAuthProviderPolicy(
    provider="approved-demo",
    client_id="public-client",
    authorization_endpoint="https://idp.example/authorize",
    token_endpoint="https://idp.example/token",
    revoke_endpoint="https://idp.example/revoke",
    scopes=("openid", "profile"),
    official_policy_url="https://idp.example/third-party-clients",
    third_party_client_allowed=True,
)


class FakeTransport:
    def __init__(self) -> None:
        self.exchange_args: dict[str, str] = {}
        self.revoked: list[str] = []

    def exchange_code(self, policy, *, code, code_verifier, redirect_uri):
        self.exchange_args = {
            "provider": policy.provider,
            "code": code,
            "code_verifier": code_verifier,
            "redirect_uri": redirect_uri,
        }
        return {
            "access_token": "access-secret",
            "refresh_token": "refresh-secret",
            "expires_in": 60,
        }

    def refresh_token(self, policy, *, refresh_token):
        assert policy.provider == "approved-demo"
        assert refresh_token == "refresh-secret"
        return {
            "access_token": "access-secret-2",
            "refresh_token": "refresh-secret-2",
            "expires_in": 60,
        }

    def revoke_token(self, policy, *, token):
        assert policy.provider == "approved-demo"
        self.revoked.append(token)


def _client(transport: FakeTransport, now: datetime | None = None) -> OAuthClient:
    return OAuthClient(
        policies=OAuthPolicyRegistry({"approved-demo": POLICY}),
        secret_store=MemorySecretStore(),
        transport=transport,
        now=lambda: now or datetime.now(UTC),
    )


def test_unapproved_provider_is_not_available_by_default() -> None:
    with pytest.raises(OAuthNotAllowedError):
        _client(FakeTransport()).start("anthropic", redirect_uri="http://127.0.0.1:43123/callback")


def test_start_uses_pkce_state_and_system_browser_hook() -> None:
    opened: list[str] = []
    client = OAuthClient(
        policies=OAuthPolicyRegistry({"approved-demo": POLICY}),
        secret_store=MemorySecretStore(),
        transport=FakeTransport(),
        browser_opener=opened.append,
    )

    authorization = client.start("approved-demo", redirect_uri="http://127.0.0.1:43123/callback")
    query = parse_qs(urlparse(authorization.authorization_url).query)

    assert opened == [authorization.authorization_url]
    assert query["state"] == [authorization.state]
    assert query["code_challenge_method"] == ["S256"]
    assert len(query["code_challenge"][0]) > 20
    assert client.callback_open(authorization.redirect_uri)


def test_callback_rejects_csrf_and_redirect_hijack_and_closes_port() -> None:
    transport = FakeTransport()
    client = _client(transport)
    authorization = client.start("approved-demo", redirect_uri="http://127.0.0.1:43123/callback")

    with pytest.raises(OAuthCallbackError):
        client.complete(
            authorization,
            code="code",
            state="wrong-state",
            redirect_uri=authorization.redirect_uri,
        )
    assert client.callback_open(authorization.redirect_uri)

    with pytest.raises(OAuthCallbackError):
        client.complete(
            authorization,
            code="code",
            state=authorization.state,
            redirect_uri="http://127.0.0.1:43124/callback",
        )
    assert not client.callback_open(authorization.redirect_uri)


def test_exchange_refresh_and_revoke_store_only_opaque_references() -> None:
    transport = FakeTransport()
    store = MemorySecretStore()
    now = datetime(2026, 7, 19, tzinfo=UTC)
    client = OAuthClient(
        policies=OAuthPolicyRegistry({"approved-demo": POLICY}),
        secret_store=store,
        transport=transport,
        now=lambda: now,
    )
    authorization = client.start("approved-demo", redirect_uri="http://127.0.0.1:43123/callback")
    credential = client.complete(
        authorization,
        code="code",
        state=authorization.state,
        redirect_uri=authorization.redirect_uri,
    )

    assert credential.access_token_ref.startswith("secret://rabbit-code/")
    assert credential.refresh_token_ref is not None
    assert store.get(credential.access_token_ref) == "access-secret"
    assert transport.exchange_args["code_verifier"]
    assert credential.is_expired(now=now + timedelta(seconds=60))

    refreshed = client.refresh(credential)
    assert store.get(refreshed.access_token_ref) == "access-secret-2"
    assert store.get(credential.access_token_ref) is None

    client.revoke(refreshed)
    assert transport.revoked == ["refresh-secret-2"]
    assert store.get(refreshed.access_token_ref) is None
