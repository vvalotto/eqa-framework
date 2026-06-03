from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from eqa_framework.architectanalyst_c.agent import main

pytestmark = pytest.mark.integration

_SAMPLE_DIR = Path(__file__).parent.parent.parent / "examples" / "sample_c_project" / "src"


def test_help_exits_zero() -> None:
    result = CliRunner().invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "ArchitectAnalyst-C" in result.output


def test_exits_zero_always(tmp_path: Path) -> None:
    result = CliRunner().invoke(
        main,
        [
            str(_SAMPLE_DIR),
            "--sprint-id",
            "sprint-01",
            "--config",
            str(tmp_path / "pyproject.toml"),
        ],
    )
    assert result.exit_code == 0


def test_text_output_contains_module_table(tmp_path: Path) -> None:
    result = CliRunner().invoke(main, [str(_SAMPLE_DIR), "--sprint-id", "sprint-01"])
    assert result.exit_code == 0
    # Module names from sample_c_project
    assert "app_logic" in result.output
    assert "hal_uart" in result.output


def test_text_output_shows_distance_findings(tmp_path: Path) -> None:
    # app_logic: Ca=2, Ce=0, I=0, A=0 → D=1.0 → ARC003 CRITICAL
    result = CliRunner().invoke(main, [str(_SAMPLE_DIR), "--sprint-id", "sprint-01"])
    assert "ARC003" in result.output
    assert "CRITICAL" in result.output


def test_json_output_is_valid(tmp_path: Path) -> None:
    result = CliRunner().invoke(
        main, [str(_SAMPLE_DIR), "--sprint-id", "sprint-01", "--format", "json"]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "metrics" in data
    assert "findings" in data
    assert isinstance(data["metrics"], list)
    assert len(data["metrics"]) > 0


def test_json_metrics_schema(tmp_path: Path) -> None:
    result = CliRunner().invoke(
        main, [str(_SAMPLE_DIR), "--sprint-id", "sprint-01", "--format", "json"]
    )
    data = json.loads(result.output)
    required_keys = {"module", "ca", "ce", "instability", "abstractness", "distance"}
    for item in data["metrics"]:
        assert required_keys.issubset(item.keys())
        assert isinstance(item["ca"], int)
        assert 0.0 <= item["instability"] <= 1.0
        assert 0.0 <= item["distance"] <= 1.0


def test_json_contains_distance_critical_finding(tmp_path: Path) -> None:
    result = CliRunner().invoke(
        main, [str(_SAMPLE_DIR), "--sprint-id", "sprint-01", "--format", "json"]
    )
    data = json.loads(result.output)
    critical = [f for f in data["findings"] if f["rule"] == "ARC003"]
    assert len(critical) >= 1
    assert critical[0]["severity"] == "CRITICAL"


def test_second_run_shows_trends(tmp_path: Path) -> None:
    """Two consecutive runs: first has no trends (=), second shows trend symbols."""
    runner = CliRunner()
    db_path = tmp_path / ".quality_control" / "arch.db"
    config_content = f"""
[tool.architectanalyst-c]
db_path = "{db_path}"
"""
    config_file = tmp_path / "pyproject.toml"
    config_file.write_text(config_content)

    runner.invoke(
        main, [str(_SAMPLE_DIR), "--sprint-id", "sprint-01", "--config", str(config_file)]
    )
    result = runner.invoke(
        main, [str(_SAMPLE_DIR), "--sprint-id", "sprint-02", "--config", str(config_file)]
    )
    assert result.exit_code == 0
    # Second run with same codebase → all deltas are 0 → show "="
    assert "=" in result.output
