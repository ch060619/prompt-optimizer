from __future__ import annotations

import json
from pathlib import Path

from backend.rabbit_code.diagnostics import DiagnosticParser, DiagnosticSeverity

# RC ID: RC-093. Verify common tool parsing, shared schema, and raw-output preservation.


def test_common_tool_diagnostics_share_file_line_column_and_severity_schema(tmp_path: Path) -> None:
    parser = DiagnosticParser(tmp_path)
    output = "".join(
        (
            "src/app.py:3:5: E501 line too long\n",
            "src/app.py:4: error: missing name\n",
            "src/App.tsx(8,2): warning TS6133 unused variable\n",
        )
    )
    report = parser.parse(("ruff", "check", "."), stdout=output, stderr="", exit_code=1)

    assert [item.file for item in report.diagnostics] == [
        Path("src/app.py"),
        Path("src/app.py"),
        Path("src/App.tsx"),
    ]
    assert [item.line for item in report.diagnostics] == [3, 4, 8]
    assert [item.column for item in report.diagnostics] == [5, None, 2]
    assert [item.severity for item in report.diagnostics] == [
        DiagnosticSeverity.ERROR,
        DiagnosticSeverity.ERROR,
        DiagnosticSeverity.WARNING,
    ]


def test_pytest_failures_and_unknown_output_keep_raw_diagnostics(tmp_path: Path) -> None:
    parser = DiagnosticParser(tmp_path)
    pytest_report = parser.parse(
        ("pytest", "tests"),
        stdout="FAILED tests/test_app.py::test_login - assertion failed\n",
        stderr="",
        exit_code=1,
    )
    assert pytest_report.diagnostics[0].file == Path("tests/test_app.py")
    assert pytest_report.diagnostics[0].severity is DiagnosticSeverity.ERROR

    raw = "tool produced an unrecognized diagnostic format"
    unknown = parser.parse(("custom-tool",), stdout=raw, stderr="stderr", exit_code=1)
    assert unknown.parse_failed
    assert unknown.stdout == raw
    assert unknown.stderr == "stderr"
    assert unknown.diagnostics[0].raw == f"{raw}\nstderr"
    assert "raw output preserved" in unknown.diagnostics[0].message


def test_diagnostic_dict_is_stable_for_cli_and_gui_consumers(tmp_path: Path) -> None:
    report = DiagnosticParser(tmp_path).parse(
        ("mypy", "backend"),
        stdout="backend/app.py:10:2: warning: deprecated API\n",
        stderr="",
        exit_code=0,
    )
    payload = report.to_dict()

    assert payload["command"] == ["mypy", "backend"]
    assert payload["diagnostics"][0]["file"] == "backend/app.py"
    assert payload["diagnostics"][0]["severity"] == "warning"
    json.dumps(payload, ensure_ascii=False)
