from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from eqa_framework.designreviewer_c.agent import main

pytestmark = pytest.mark.integration

_SAMPLE_DIR = Path(__file__).parent.parent.parent / "examples" / "sample_c_project" / "src"


def test_help_exits_zero() -> None:
    result = CliRunner().invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "DesignReviewer-C" in result.output


def test_exits_one_on_critical_findings() -> None:
    # sample_c_project has hal_uart.c including app_logic.h — LAY001 CRITICAL
    result = CliRunner().invoke(main, [str(_SAMPLE_DIR)])
    assert result.exit_code == 1


def test_text_output_reports_layer_violation() -> None:
    result = CliRunner().invoke(main, [str(_SAMPLE_DIR)])
    # The finding message always contains "layer 'hal'" even when Rule column is truncated
    assert "hal" in result.output
    assert "CRITICAL" in result.output


def test_json_output_is_valid() -> None:
    result = CliRunner().invoke(main, [str(_SAMPLE_DIR), "--format", "json"])
    assert result.exit_code == 1
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) > 0


def test_json_output_schema() -> None:
    result = CliRunner().invoke(main, [str(_SAMPLE_DIR), "--format", "json"])
    data = json.loads(result.output)
    required_keys = {"file", "line", "severity", "rule", "message", "tool"}
    for item in data:
        assert required_keys.issubset(item.keys())
        assert isinstance(item["line"], int)
        assert item["severity"] in ("CRITICAL", "ERROR", "WARNING", "INFO")


def test_json_contains_layer_violation() -> None:
    result = CliRunner().invoke(main, [str(_SAMPLE_DIR), "--format", "json"])
    data = json.loads(result.output)
    layer_findings = [f for f in data if f["rule"] == "LAY001"]
    assert len(layer_findings) >= 1
    assert layer_findings[0]["severity"] == "CRITICAL"


def test_single_file_exits_zero_when_no_violations() -> None:
    # main.c is not in any defined layer — no violations expected
    main_c = _SAMPLE_DIR / "main.c"
    result = CliRunner().invoke(main, [str(main_c)])
    assert result.exit_code == 0
