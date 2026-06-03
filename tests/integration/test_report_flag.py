from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from eqa_framework.architectanalyst_c.agent import main as architectanalyst_main
from eqa_framework.codeguard_c.agent import main as codeguard_main
from eqa_framework.designreviewer_c.agent import main as designreviewer_main

pytestmark = pytest.mark.integration

_SAMPLE = Path(__file__).parent.parent.parent / "examples" / "sample_c_project" / "src"


class TestCodeGuardReport:
    def test_report_to_stdout(self) -> None:
        runner = CliRunner()
        result = runner.invoke(codeguard_main, [str(_SAMPLE), "--report"])
        assert result.exit_code == 0
        assert "# CodeGuard-C — Perfil de Calidad" in result.output

    def test_report_to_file(self, tmp_path: Path) -> None:
        out = tmp_path / "report.md"
        runner = CliRunner()
        result = runner.invoke(codeguard_main, [str(_SAMPLE), "--report", str(out)])
        assert result.exit_code == 0
        assert out.exists()
        content = out.read_text(encoding="utf-8")
        assert "# CodeGuard-C — Perfil de Calidad" in content

    def test_report_contains_profile_table(self) -> None:
        runner = CliRunner()
        result = runner.invoke(codeguard_main, [str(_SAMPLE), "--report"])
        assert "## Perfil" in result.output
        assert "| Dimensión" in result.output

    def test_report_contains_summary(self) -> None:
        runner = CliRunner()
        result = runner.invoke(codeguard_main, [str(_SAMPLE), "--report"])
        assert "## Resumen" in result.output

    def test_without_report_flag_no_markdown(self) -> None:
        runner = CliRunner()
        result = runner.invoke(codeguard_main, [str(_SAMPLE)])
        assert result.exit_code == 0
        assert "# CodeGuard-C — Perfil de Calidad" not in result.output


class TestDesignReviewerReport:
    def test_report_to_stdout(self) -> None:
        runner = CliRunner()
        result = runner.invoke(designreviewer_main, [str(_SAMPLE), "--report"])
        assert result.exit_code in (0, 1)  # puede tener CRITICAL pero no falla el reporte
        assert "# DesignReviewer-C — Perfil de Calidad" in result.output

    def test_report_to_file(self, tmp_path: Path) -> None:
        out = tmp_path / "report.md"
        runner = CliRunner()
        runner.invoke(designreviewer_main, [str(_SAMPLE), "--report", str(out)])
        assert out.exists()
        content = out.read_text(encoding="utf-8")
        assert "# DesignReviewer-C — Perfil de Calidad" in content

    def test_report_contains_dimensions(self) -> None:
        runner = CliRunner()
        result = runner.invoke(designreviewer_main, [str(_SAMPLE), "--report"])
        assert "Dependencias" in result.output or "Capas" in result.output


class TestArchitectAnalystReport:
    def test_report_to_stdout(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            architectanalyst_main,
            [str(_SAMPLE), "--report", "--config", str(_SAMPLE.parent / "pyproject.toml")],
        )
        assert result.exit_code == 0
        assert "# ArchitectAnalyst-C — Perfil de Calidad" in result.output

    def test_report_to_file(self, tmp_path: Path) -> None:
        out = tmp_path / "report.md"
        runner = CliRunner()
        result = runner.invoke(
            architectanalyst_main,
            [
                str(_SAMPLE),
                "--report",
                str(out),
                "--config",
                str(_SAMPLE.parent / "pyproject.toml"),
            ],
        )
        assert result.exit_code == 0
        assert out.exists()
        content = out.read_text(encoding="utf-8")
        assert "# ArchitectAnalyst-C — Perfil de Calidad" in content

    def test_report_contains_dimensions(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            architectanalyst_main,
            [str(_SAMPLE), "--report", "--config", str(_SAMPLE.parent / "pyproject.toml")],
        )
        assert "Inestabilidad" in result.output or "Distancia" in result.output
