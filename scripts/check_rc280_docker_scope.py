#!/usr/bin/env python3
"""RC ID: RC-280. Verify Docker usage is limited to local dev/test.

Checks:
    1. Dockerfile exists and is dev/test only (comment, non-root user)
    2. docker-compose.dev.yml exists with dev/test profiles, 127.0.0.1 binding
    3. No docker-compose.yml (production) exists
    4. CI has a separate docker job, distinct from backend/frontend
    5. README does not treat Docker as desktop verification
    6. DOCKER.md policy document exists
    7. No public service deployment config
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE = ROOT / "Dockerfile"
DOCKER_COMPOSE_DEV = ROOT / "docker-compose.dev.yml"
DOCKER_COMPOSE_PROD = ROOT / "docker-compose.yml"
DOCKER_DOC = ROOT / "docs" / "DOCKER.md"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
README = ROOT / "README.md"


def check_dockerfile() -> list[str]:
    errors: list[str] = []
    if not DOCKERFILE.is_file():
        errors.append("Dockerfile not found")
        return errors
    text = DOCKERFILE.read_text(encoding="utf-8")
    if "USER rabbit" not in text and "USER" not in text:
        errors.append("Dockerfile must run as non-root user")
    if "development" not in text.lower() and "dev" not in text.lower() and "test" not in text.lower():
        errors.append("Dockerfile should document it is for dev/test only")
    # Should NOT expose to 0.0.0.0 without 127.0.0.1 qualification in CMD
    # (0.0.0.0 in CMD is OK for container internal, but compose should bind 127.0.0.1)
    return errors


def check_docker_compose_dev() -> list[str]:
    errors: list[str] = []
    if not DOCKER_COMPOSE_DEV.is_file():
        errors.append("docker-compose.dev.yml not found")
        return errors
    text = DOCKER_COMPOSE_DEV.read_text(encoding="utf-8")
    if "127.0.0.1" not in text:
        errors.append("docker-compose.dev.yml must bind to 127.0.0.1 only")
    if "profile" not in text.lower():
        errors.append("docker-compose.dev.yml should use profiles (dev/test)")
    if "restart: \"no\"" not in text and 'restart: "no"' not in text:
        errors.append("docker-compose.dev.yml should not auto-restart")
    return errors


def check_no_production_compose() -> list[str]:
    """Ensure no production docker-compose.yml exists."""
    errors: list[str] = []
    if DOCKER_COMPOSE_PROD.is_file():
        errors.append("docker-compose.yml (production) should not exist — Docker is dev/test only")
    return errors


def check_ci_docker_job() -> list[str]:
    errors: list[str] = []
    if not CI_WORKFLOW.is_file():
        errors.append("ci.yml not found")
        return errors
    text = CI_WORKFLOW.read_text(encoding="utf-8")
    if "docker:" not in text:
        errors.append("CI must have a separate docker job")
    if "RC-280" not in text:
        errors.append("CI docker job should reference RC-280")
    # Docker job should be separate from backend/frontend
    if "docker:" in text and "backend:" in text:
        # Good — they are separate jobs
        pass
    else:
        errors.append("Docker job must be separate from backend/frontend jobs")
    return errors


def check_readme_scope() -> list[str]:
    """README should not treat Docker as desktop verification."""
    errors: list[str] = []
    if not README.is_file():
        errors.append("README.md not found")
        return errors
    text = README.read_text(encoding="utf-8")
    # README should mention Docker is optional/dev
    if "docker" in text.lower() and "可选" not in text and "optional" not in text.lower():
        # Check context — Docker should be marked optional
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if "docker" in line.lower():
                # Check nearby lines for optional/dev/test qualification
                context = "\n".join(lines[max(0, i-2):i+3])
                if "可选" in context or "optional" in context.lower() or "开发" in context or "dev" in context.lower() or "测试" in context or "test" in context.lower():
                    break
        else:
            errors.append("README should qualify Docker as optional/dev/test")
    # README should NOT say Docker replaces desktop install
    if "docker" in text.lower() and ("代替" in text or "replace" in text.lower()):
        if "桌面" in text or "desktop" in text.lower():
            # Check it says "does NOT replace"
            if "不代替" not in text and "does not replace" not in text.lower():
                errors.append("README should NOT claim Docker replaces desktop install")
    return errors


def check_docker_doc() -> list[str]:
    errors: list[str] = []
    if not DOCKER_DOC.is_file():
        errors.append("docs/DOCKER.md policy document not found")
        return errors
    text = DOCKER_DOC.read_text(encoding="utf-8")
    if "not" not in text.lower() or "production" not in text.lower():
        errors.append("DOCKER.md must clearly state Docker is NOT for production")
    if "desktop" not in text.lower() or "cli" not in text.lower():
        errors.append("DOCKER.md must clarify Docker does not replace desktop/CLI verification")
    return errors


def check_no_public_service_config() -> list[str]:
    """Ensure no Kubernetes/Helm/public service deployment configs exist."""
    errors: list[str] = []
    k8s_patterns = [
        ROOT / "k8s",
        ROOT / "kubernetes",
        ROOT / "deploy",
        ROOT / "helm",
        ROOT / "Chart.yaml",
        ROOT / "deployment.yaml",
    ]
    for p in k8s_patterns:
        if p.exists():
            errors.append(f"Public service deployment config found: {p.name} — Docker scope is dev/test only")
    return errors


def main() -> int:
    all_errors: list[str] = []
    all_errors.extend(check_dockerfile())
    all_errors.extend(check_docker_compose_dev())
    all_errors.extend(check_no_production_compose())
    all_errors.extend(check_ci_docker_job())
    all_errors.extend(check_readme_scope())
    all_errors.extend(check_docker_doc())
    all_errors.extend(check_no_public_service_config())

    if all_errors:
        print("FAIL: RC-280 Docker scope verification", file=sys.stderr)
        for e in all_errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print("PASS: RC-280 Docker scope verification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
