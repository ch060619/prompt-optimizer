from __future__ import annotations

from fastapi.testclient import TestClient

from prompt_optimizer.api.app import create_app


def test_api_analyze() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/analyze",
        json={"prompt": "你是一名老师，请解释机器学习，输出格式为列表。"},
    )
    assert response.status_code == 200
    assert response.json()["score"]["total_score"] >= 0


def test_api_templates() -> None:
    client = TestClient(create_app())
    response = client.get("/api/templates?category=business")
    assert response.status_code == 200
    assert response.json()


def test_api_optimize_and_export() -> None:
    client = TestClient(create_app())
    response = client.post("/api/optimize", json={"prompt": "帮我写销售话术"})
    assert response.status_code == 200
    version_id = response.json()["version_id"]

    export_response = client.post("/api/export", json={"version_id": version_id, "format": "md"})
    assert export_response.status_code == 200
    assert "提示词优化结果" in export_response.text
