from __future__ import annotations

from pathlib import Path

import pytest

from eqa_framework.shared.config import load_toml_section

pytestmark = pytest.mark.integration


def _pyproject(project: Path, content: str) -> None:
    (project / "pyproject.toml").write_text(content, encoding="utf-8")


def _personal(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


class TestLoadTomlSectionWithRealFiles:
    """load_toml_section fusiona correctamente archivos TOML reales en disco."""

    def test_codeguard_personal_overrides_project(self, tmp_path: Path) -> None:
        _pyproject(tmp_path, "[tool.codeguard-c]\nmax_cyclomatic_complexity = 12\n")
        personal = _personal(
            tmp_path / "personal.toml",
            "[codeguard-c]\nmax_cyclomatic_complexity = 7\n",
        )

        result = load_toml_section(tmp_path, "codeguard-c", personal_config_path=personal)

        assert result["max_cyclomatic_complexity"] == 7

    def test_designreviewer_personal_adds_key(self, tmp_path: Path) -> None:
        _pyproject(tmp_path, "[tool.designreviewer-c]\nmax_fan_out = 10\n")
        personal = _personal(
            tmp_path / "personal.toml",
            "[designreviewer-c]\nmax_parameters = 3\n",
        )

        result = load_toml_section(tmp_path, "designreviewer-c", personal_config_path=personal)

        assert result["max_fan_out"] == 10
        assert result["max_parameters"] == 3

    def test_architectanalyst_personal_float(self, tmp_path: Path) -> None:
        _pyproject(tmp_path, "[tool.architectanalyst-c]\nmax_instability = 0.8\n")
        personal = _personal(
            tmp_path / "personal.toml",
            "[architectanalyst-c]\nmax_instability = 0.4\n",
        )

        result = load_toml_section(tmp_path, "architectanalyst-c", personal_config_path=personal)

        assert result["max_instability"] == pytest.approx(0.4)

    def test_all_three_agents_independent(self, tmp_path: Path) -> None:
        _pyproject(
            tmp_path,
            "[tool.codeguard-c]\nmax_cyclomatic_complexity = 12\n"
            "[tool.designreviewer-c]\nmax_fan_out = 10\n"
            "[tool.architectanalyst-c]\nmax_instability = 0.8\n",
        )
        personal = _personal(
            tmp_path / "personal.toml",
            "[codeguard-c]\nmax_cyclomatic_complexity = 6\n"
            "[architectanalyst-c]\nmax_instability = 0.3\n",
        )

        cg = load_toml_section(tmp_path, "codeguard-c", personal_config_path=personal)
        dr = load_toml_section(tmp_path, "designreviewer-c", personal_config_path=personal)
        aa = load_toml_section(tmp_path, "architectanalyst-c", personal_config_path=personal)

        assert cg["max_cyclomatic_complexity"] == 6
        assert dr["max_fan_out"] == 10
        assert "max_instability" not in dr
        assert aa["max_instability"] == pytest.approx(0.3)
