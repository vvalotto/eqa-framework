from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from eqa_framework.codeguard_c.agent import main

pytestmark = pytest.mark.integration

_SAMPLE_DIR = Path(__file__).parent.parent.parent / "examples" / "sample_c_project" / "src"


def test_help_exits_zero() -> None:
    result = CliRunner().invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "CodeGuard-C" in result.output


def test_text_output_exits_zero() -> None:
    result = CliRunner().invoke(main, [str(_SAMPLE_DIR)])
    assert result.exit_code == 0


def test_text_output_contains_findings() -> None:
    result = CliRunner().invoke(main, [str(_SAMPLE_DIR)])
    # sensor.c has gets() and strcpy() — flawfinder must detect them
    output = result.output
    assert any(kw in output for kw in ("gets", "strcpy", "ERROR", "CRITICAL", "WARNING"))


def test_json_output_is_valid() -> None:
    result = CliRunner().invoke(main, [str(_SAMPLE_DIR), "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)


def test_json_output_schema() -> None:
    result = CliRunner().invoke(main, [str(_SAMPLE_DIR), "--format", "json"])
    data = json.loads(result.output)
    assert len(data) > 0
    required_keys = {"file", "line", "severity", "rule", "message", "tool"}
    for item in data:
        assert required_keys.issubset(item.keys())
        assert isinstance(item["line"], int)
        assert item["severity"] in ("CRITICAL", "ERROR", "WARNING", "INFO")


def test_json_contains_security_findings() -> None:
    result = CliRunner().invoke(main, [str(_SAMPLE_DIR), "--format", "json"])
    data = json.loads(result.output)
    tools = {item["tool"] for item in data}
    assert "flawfinder" in tools


def test_single_file_mode() -> None:
    sensor = _SAMPLE_DIR / "sensor.c"
    result = CliRunner().invoke(main, [str(sensor)])
    assert result.exit_code == 0
