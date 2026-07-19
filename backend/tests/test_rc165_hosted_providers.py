from __future__ import annotations

import httpx

from prompt_optimizer.providers import (
    AzureOpenAIAdapter,
    BedrockConverseAdapter,
    ModelRequest,
    ProviderConfig,
    ProviderRegistry,
    VertexAIAdapter,
)

# RC ID: RC-165. Verify hosted-provider endpoints, credentials, regions, and deployment mapping.


def test_azure_openai_uses_deployment_endpoint_and_api_key_header() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == (
            "https://azure.example/openai/deployments/deploy-1/chat/completions"
            "?api-version=2024-10-21"
        )
        assert request.headers["api-key"] == "azure-key"
        assert "Authorization" not in request.headers
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "目标：Azure。"}}]},
        )

    provider = AzureOpenAIAdapter(
        ProviderConfig(
            name="azure",
            base_url="https://azure.example",
            api_key="azure-key",
            model="gpt-4o",
            deployment="deploy-1",
            api_version="2024-10-21",
            api_protocol="azure_openai",
            max_retries=0,
        ),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    result = provider.optimize(ModelRequest(prompt="整理 Azure 版本"))
    assert result.analysis.optimized_prompt == "目标：Azure。"


def test_vertex_uses_project_region_bearer_and_gemini_parts() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == (
            "/v1/projects/project-1/locations/us-central1/publishers/google/"
            "models/gemini-2.0-flash:generateContent"
        )
        assert request.headers["Authorization"] == "Bearer vertex-token"
        assert b"contents" in request.read()
        return httpx.Response(
            200,
            json={"candidates": [{"content": {"parts": [{"text": "目标：Vertex。"}]}}]},
        )

    provider = VertexAIAdapter(
        ProviderConfig(
            name="vertex",
            base_url="https://aiplatform.googleapis.com",
            api_key="vertex-token",
            model="gemini-2.0-flash",
            project_id="project-1",
            region="us-central1",
            api_protocol="vertex",
            max_retries=0,
        ),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    result = provider.optimize(ModelRequest(prompt="整理 Vertex 版本"))
    assert result.analysis.optimized_prompt == "目标：Vertex。"


def test_bedrock_uses_converse_endpoint_and_injected_sigv4_signer() -> None:
    signed: list[tuple[str, str, bytes]] = []

    def signer(method: str, url: str, headers: dict[str, str], body: bytes) -> dict[str, str]:
        signed.append((method, url, body))
        return {**headers, "Authorization": "AWS4-HMAC-SHA256 mock"}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/model/amazon.nova-lite-v1/converse"
        assert request.headers["Authorization"].startswith("AWS4-HMAC-SHA256")
        return httpx.Response(
            200,
            json={
                "output": {"message": {"content": [{"text": "目标：Bedrock。"}]}},
                "usage": {"inputTokens": 4},
            },
        )

    provider = BedrockConverseAdapter(
        ProviderConfig(
            name="bedrock",
            base_url="https://bedrock-runtime.us-east-1.amazonaws.com",
            api_key="aws-credential-ref",
            model="amazon.nova-lite-v1",
            region="us-east-1",
            api_protocol="bedrock",
            credential_mode="aws_sigv4",
            max_retries=0,
        ),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        signer=signer,
    )

    response = provider.optimize(ModelRequest(prompt="整理 Bedrock 版本"))
    assert response.analysis.optimized_prompt == "目标：Bedrock。"
    assert signed and signed[0][0] == "POST"


def test_registry_selects_hosted_variants_by_provider_name(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    common = {
        "BASE_URL": "https://example.test",
        "API_KEY": "credential",
        "MODEL": "model",
        "AUTHORIZED": "true",
    }
    for name, expected in {
        "azure": AzureOpenAIAdapter,
        "vertex": VertexAIAdapter,
        "bedrock": BedrockConverseAdapter,
    }.items():
        for suffix, value in common.items():
            monkeypatch.setenv(f"RABBIT_CODE_{name.upper()}_{suffix}", value)
        provider = ProviderRegistry().get(name)
        assert isinstance(provider, expected)
