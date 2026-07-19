from __future__ import annotations

from prompt_optimizer.providers import (
    DEFAULT_RUNNER,
    RUNNER_COMPARISON,
    RunnerRegistry,
)
from prompt_optimizer.providers.base import ModelRequest
from prompt_optimizer.providers.local import LocalModelNotInstalled

# RC ID: RC-187. Verify the same lifecycle contract for default and alternate runners.


def test_runner_strategy_records_default_and_license_audited_alternative() -> None:
    assert DEFAULT_RUNNER == "ollama"
    assert {item["id"] for item in RUNNER_COMPARISON} == {"ollama", "llama-cpp"}
    assert all(item["license"] == "MIT" for item in RUNNER_COMPARISON)


def test_default_and_alternate_share_pull_load_generate_stop_list_remove_health() -> None:
    for runner_name in ("ollama", "llama-cpp"):
        runner = RunnerRegistry().create(runner_name)
        assert runner.health().status == "not_installed"
        try:
            runner.generate(ModelRequest(prompt="test"))
        except LocalModelNotInstalled:
            pass
        else:
            raise AssertionError("uninstalled runner must reject generation")

        assert runner.pull("gemma-3-1b").status == "ok"
        assert runner.load("gemma-3-1b").status == "ok"
        assert runner.health().ready is True
        assert runner.generate(ModelRequest(prompt="test")) == f"[{runner_name}] test"
        assert list(runner.stream(ModelRequest(prompt="stream test"))) == [
            f"[{runner_name}]",
            "stream",
            "test",
        ]
        assert runner.list()[0].loaded is True
        assert runner.stop("gemma-3-1b").status == "ok"
        assert runner.health().status == "not_ready"
        assert runner.remove("gemma-3-1b").status == "ok"
        assert runner.list() == ()
