from __future__ import annotations

import sys

from typer.testing import CliRunner

from prompt_optimizer.cli.app import app, compatibility_notice

# RC ID: RC-051. Verify rabbit prompt wrappers and prompt-opt migration behavior.


runner = CliRunner()


def test_rabbit_prompt_analyze_matches_flat_command() -> None:
    prompt = "请用列表解释机器学习。"

    flat = runner.invoke(app, ["analyze", prompt])
    grouped = runner.invoke(app, ["prompt", "analyze", prompt])

    assert flat.exit_code == 0
    assert grouped.exit_code == 0
    assert grouped.stdout == flat.stdout
    assert "总分" in grouped.stdout


def test_rabbit_prompt_templates_preserves_old_command_output() -> None:
    flat = runner.invoke(app, ["templates", "list", "--category", "tech"])
    grouped = runner.invoke(app, ["prompt", "templates", "list", "--category", "tech"])

    assert flat.exit_code == 0
    assert grouped.exit_code == 0
    assert grouped.stdout == flat.stdout
    assert "tech-code-generation" in grouped.stdout


def test_prompt_opt_alias_emits_migration_warning(monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(sys, "argv", ["prompt-opt"])

    compatibility_notice()

    captured = capsys.readouterr()
    assert "prompt-opt" in captured.err
    assert "rabbit" in captured.err
    assert "3.0.0" in captured.err
