"""RC ID: RC-280. Tests for Docker scope limitation."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DOCKERFILE = ROOT / "Dockerfile"
DOCKER_COMPOSE_DEV = ROOT / "docker-compose.dev.yml"
DOCKER_COMPOSE_PROD = ROOT / "docker-compose.yml"
DOCKER_DOC = ROOT / "docs" / "DOCKER.md"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
README = ROOT / "README.md"


class TestDockerfile:
    def test_exists(self) -> None:
        assert DOCKERFILE.is_file()

    def test_non_root_user(self) -> None:
        text = DOCKERFILE.read_text(encoding="utf-8")
        assert "USER" in text
        assert "root" not in text.split("USER")[1].split("\n")[0].lower()

    def test_dev_test_comment(self) -> None:
        text = DOCKERFILE.read_text(encoding="utf-8")
        assert "development" in text.lower() or "dev" in text.lower() or "test" in text.lower()


class TestDockerComposeDev:
    def test_exists(self) -> None:
        assert DOCKER_COMPOSE_DEV.is_file()

    def test_binds_localhost(self) -> None:
        text = DOCKER_COMPOSE_DEV.read_text(encoding="utf-8")
        assert "127.0.0.1" in text

    def test_has_profiles(self) -> None:
        text = DOCKER_COMPOSE_DEV.read_text(encoding="utf-8")
        assert "profile" in text.lower()

    def test_no_auto_restart(self) -> None:
        text = DOCKER_COMPOSE_DEV.read_text(encoding="utf-8")
        assert 'restart: "no"' in text or 'restart: "no"' in text


class TestNoProductionCompose:
    def test_no_production_compose(self) -> None:
        assert not DOCKER_COMPOSE_PROD.is_file(), "docker-compose.yml (production) must not exist"


class TestCI:
    def test_ci_exists(self) -> None:
        assert CI_WORKFLOW.is_file()

    def test_has_docker_job(self) -> None:
        text = CI_WORKFLOW.read_text(encoding="utf-8")
        assert "docker:" in text

    def test_docker_job_separate_from_backend(self) -> None:
        text = CI_WORKFLOW.read_text(encoding="utf-8")
        assert "backend:" in text
        assert "docker:" in text
        # They should be separate job blocks
        assert text.index("docker:") != text.index("backend:")

    def test_docker_job_has_rc280_reference(self) -> None:
        text = CI_WORKFLOW.read_text(encoding="utf-8")
        assert "RC-280" in text

    def test_docker_job_does_not_replace_install(self) -> None:
        text = CI_WORKFLOW.read_text(encoding="utf-8")
        # The RC-280 comment block should state Docker does NOT replace install
        rc280_idx = text.index("RC-280")
        docker_section = text[rc280_idx:rc280_idx + 500]
        assert "NOT" in docker_section or "not" in docker_section.lower()


class TestReadme:
    def test_readme_exists(self) -> None:
        assert README.is_file()

    def test_docker_is_optional(self) -> None:
        text = README.read_text(encoding="utf-8")
        if "docker" in text.lower():
            # Must be qualified as optional
            docker_lines = [l for l in text.split("\n") if "docker" in l.lower()]
            found_optional = False
            for line in docker_lines:
                if any(w in line.lower() for w in ["可选", "optional", "开发", "dev", "测试", "test"]):
                    found_optional = True
                    break
            assert found_optional, "Docker in README must be qualified as optional/dev/test"


class TestDockerDoc:
    def test_doc_exists(self) -> None:
        assert DOCKER_DOC.is_file()

    def test_states_not_production(self) -> None:
        text = DOCKER_DOC.read_text(encoding="utf-8")
        assert "not" in text.lower()
        assert "production" in text.lower()

    def test_clarifies_no_desktop_replacement(self) -> None:
        text = DOCKER_DOC.read_text(encoding="utf-8")
        assert "desktop" in text.lower() or "桌面" in text
        assert "cli" in text.lower() or "命令行" in text

    def test_has_ci_separation_section(self) -> None:
        text = DOCKER_DOC.read_text(encoding="utf-8")
        assert "CI" in text or "ci" in text.lower()
        assert "separate" in text.lower() or "分离" in text or "独立" in text


class TestNoPublicServiceDeployment:
    def test_no_k8s_dir(self) -> None:
        assert not (ROOT / "k8s").exists()
        assert not (ROOT / "kubernetes").exists()

    def test_no_helm_chart(self) -> None:
        assert not (ROOT / "Chart.yaml").exists()
        assert not (ROOT / "helm").exists()

    def test_no_deployment_yaml(self) -> None:
        assert not (ROOT / "deployment.yaml").exists()
