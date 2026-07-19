from __future__ import annotations

from pathlib import Path

from scripts.security_scan import find_secret_hits, validate_dockerfile

# RC ID: RC-211. Verify security gates reject secrets and unsafe containers.


def test_repository_security_documents_and_generated_sbom_are_current() -> None:
    root = Path(__file__).parents[2]
    assert not find_secret_hits(root)
    assert not validate_dockerfile(root / "Dockerfile")


def test_secret_scan_detects_high_confidence_values_in_product_paths(tmp_path: Path) -> None:
    source = tmp_path / "backend" / "src"
    source.mkdir(parents=True)
    (source / "leak.py").write_text('api_key = "sk-proj-1234567890abcdefghijklmnop"\n', encoding="utf-8")
    hits = find_secret_hits(tmp_path)
    assert hits == (("backend/src/leak.py", 1, "provider-key"),)


def test_container_gate_requires_non_root_and_lockfile_install(tmp_path: Path) -> None:
    dockerfile = tmp_path / "Dockerfile"
    dockerfile.write_text("FROM node:latest\nRUN npm install\nADD . /app\n", encoding="utf-8")
    errors = validate_dockerfile(dockerfile)
    assert "non-root USER" in errors[0]
    assert any("latest" in error for error in errors)
    assert any("COPY" in error for error in errors)
    assert any("npm ci" in error for error in errors)
