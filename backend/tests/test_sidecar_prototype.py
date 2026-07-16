from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

# RC ID: RC-046. Validate the stack decision and the minimal sidecar lifecycle.
# RC ID: RC-054. Validate the canonical Rabbit Code sidecar data directory.
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PROTOTYPE_PATH = REPOSITORY_ROOT / "scripts" / "prototypes" / "sidecar_probe.py"
SPEC = importlib.util.spec_from_file_location("sidecar_probe", PROTOTYPE_PATH)
assert SPEC is not None and SPEC.loader is not None
sidecar_probe = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = sidecar_probe
SPEC.loader.exec_module(sidecar_probe)


def test_sidecar_starts_on_loopback_and_stops_without_a_residual_process(
    tmp_path: Path,
) -> None:
    result = sidecar_probe.run_probe(
        python_executable=sys.executable,
        data_dir=tmp_path,
        timeout_seconds=10.0,
    )

    assert result["host"] == "127.0.0.1"
    assert 0 < result["port"] < 65536
    assert result["ready"] is True
    assert result["startup_ms"] < 10_000
    assert result["alive_after_shutdown"] is False
    assert (tmp_path / "rabbit-code.sqlite3").is_file()


def test_stack_adr_covers_required_decisions_and_alternatives() -> None:
    content = (
        REPOSITORY_ROOT / "docs" / "adr" / "0002-technology-stack-retention.md"
    ).read_text(encoding="utf-8")

    assert "- Status: Accepted" in content
    assert "## 基准数据" in content
    assert "## 备选方案" in content
    assert "## 替换触发条件" in content
    for technology in (
        "Python",
        "FastAPI",
        "React",
        "Vite",
        "TypeScript",
        "SQLite",
        "Typer",
        "Docker",
    ):
        assert f"| {technology} |" in content


def test_stack_benchmark_records_real_sidecar_and_local_storage_results() -> None:
    payload = json.loads(
        (REPOSITORY_ROOT / "docs" / "benchmarks" / "rc-046-windows.json").read_text(
            encoding="utf-8"
        )
    )

    assert payload["rc_id"] == "RC-046"
    assert payload["git_commit"]
    assert payload["sidecar"]["ready"] is True
    assert payload["sidecar"]["alive_after_shutdown"] is False
    assert payload["sqlite"]["rows"] == 5_000
    assert payload["frontend_dist"]["files"] > 0
    assert payload["versions"]["docker_cli"]["summary"]
