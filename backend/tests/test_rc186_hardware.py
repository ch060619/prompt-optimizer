from __future__ import annotations

from pathlib import Path

from prompt_optimizer.hardware import HardwareDetector

# RC ID: RC-186. Verify stable fields, degraded probes, redaction, and corrections.


def test_hardware_report_is_stable_and_contains_sources(tmp_path: Path) -> None:
    files = {
        Path("/proc/cpuinfo"): "model name: Test CPU\n",
        Path("/proc/meminfo"): "MemTotal:       4096 kB\n",
    }

    def read_file(path: Path) -> str:
        return files[path]

    def command(arguments: tuple[str, ...] | list[str]) -> tuple[int, str, str]:
        if "nvidia-smi" in arguments[0]:
            return 0, "Test GPU, 8192, 555.1\n", ""
        return 0, "ollama version 0.3\n", ""

    def locate(name: str) -> str | None:
        return f"/usr/bin/{name}" if name in {"nvidia-smi", "ollama"} else None

    detector = HardwareDetector(
        root=tmp_path,
        file_reader=read_file,
        command_runner=command,
        which_reader=locate,
        network_probe=lambda: True,
        environment={"HTTPS_PROXY": "https://user:secret@proxy.test:8443", "NO_PROXY": "localhost"},
    )

    report = detector.detect()
    first = report.to_json()
    second = report.to_json()
    assert first == second
    assert report.fields["gpu"].value == {
        "devices": [{"driver": "555.1", "memory_mb": 8192, "name": "Test GPU"}],
        "detected": True,
    }
    assert report.fields["ram"].value == {"total_bytes": 4096 * 1024}
    assert report.fields["proxy"].value == {
        "configured": True,
        "entries": [{"endpoint": "https://proxy.test:8443", "name": "https_proxy"}],
        "no_proxy": ["localhost"],
    }
    assert "secret" not in report.to_json()


def test_permission_failures_degrade_and_user_corrections_are_explicit(tmp_path: Path) -> None:
    def denied(_: Path) -> str:
        raise PermissionError("denied")

    report = HardwareDetector(
        root=tmp_path,
        file_reader=denied,
        which_reader=lambda _: None,
        network_probe=lambda: False,
    ).detect({"ram": {"total_bytes": 123}, "gpu": {"devices": []}})

    assert report.fields["ram"].source == "user"
    assert report.fields["ram"].confidence == "user"
    assert report.fields["ram"].value == {"total_bytes": 123}
    assert report.fields["network"].value == {"dns_resolution": False}
    assert report.fields["runners"].value == {
        "ollama": {"installed": False, "path": None, "version": None},
        "llama-cpp": {"installed": False, "path": None, "version": None},
    }


def test_runner_path_permission_failure_degrades(tmp_path: Path) -> None:
    def denied(_: str) -> str | None:
        raise PermissionError("denied")

    report = HardwareDetector(root=tmp_path, which_reader=denied).detect()
    assert report.fields["runners"].confidence == "medium"
    assert all(not item["installed"] for item in report.fields["runners"].value.values())
