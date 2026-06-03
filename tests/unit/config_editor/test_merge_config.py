from __future__ import annotations

from pathlib import Path

import pytest

from eqa_framework.shared.config import load_toml_section


def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


class TestMergePrecedence:
    """Personal gana sobre proyecto, proyecto gana sobre defaults."""

    def test_personal_wins_over_project(self, tmp_path: Path) -> None:
        project = tmp_path / "proj"
        project.mkdir()
        _write(project / "pyproject.toml", "[tool.codeguard-c]\nmax_cyclomatic_complexity = 12\n")
        personal = _write(tmp_path / "p.toml", "[codeguard-c]\nmax_cyclomatic_complexity = 8\n")

        result = load_toml_section(project, "codeguard-c", personal_config_path=personal)

        assert result["max_cyclomatic_complexity"] == 8

    def test_project_wins_over_defaults_when_no_personal(self, tmp_path: Path) -> None:
        project = tmp_path / "proj"
        project.mkdir()
        _write(project / "pyproject.toml", "[tool.codeguard-c]\nmax_cyclomatic_complexity = 20\n")
        personal = tmp_path / "empty.toml"

        result = load_toml_section(project, "codeguard-c", personal_config_path=personal)

        assert result["max_cyclomatic_complexity"] == 20

    def test_defaults_when_no_project_no_personal(self, tmp_path: Path) -> None:
        project = tmp_path / "proj"
        project.mkdir()
        personal = tmp_path / "empty.toml"

        result = load_toml_section(project, "codeguard-c", personal_config_path=personal)

        assert result == {}

    def test_apply_personal_false_ignores_personal(self, tmp_path: Path) -> None:
        project = tmp_path / "proj"
        project.mkdir()
        _write(project / "pyproject.toml", "[tool.codeguard-c]\nmax_cyclomatic_complexity = 12\n")
        personal = _write(tmp_path / "p.toml", "[codeguard-c]\nmax_cyclomatic_complexity = 5\n")

        result = load_toml_section(
            project, "codeguard-c", apply_personal=False, personal_config_path=personal
        )

        assert result["max_cyclomatic_complexity"] == 12

    def test_merge_is_per_key_not_per_section(self, tmp_path: Path) -> None:
        project = tmp_path / "proj"
        project.mkdir()
        _write(
            project / "pyproject.toml",
            "[tool.codeguard-c]\nmax_cyclomatic_complexity = 12\nmax_function_lines = 50\n",
        )
        personal = _write(
            tmp_path / "p.toml",
            "[codeguard-c]\nmax_cyclomatic_complexity = 8\n",
        )

        result = load_toml_section(project, "codeguard-c", personal_config_path=personal)

        assert result["max_cyclomatic_complexity"] == 8
        assert result["max_function_lines"] == 50

    def test_personal_key_for_different_agent_not_applied(self, tmp_path: Path) -> None:
        project = tmp_path / "proj"
        project.mkdir()
        _write(project / "pyproject.toml", "[tool.codeguard-c]\nmax_cyclomatic_complexity = 12\n")
        personal = _write(
            tmp_path / "p.toml",
            "[architectanalyst-c]\nmax_instability = 0.5\n",
        )

        result = load_toml_section(project, "codeguard-c", personal_config_path=personal)

        assert result == {"max_cyclomatic_complexity": 12}
        assert "max_instability" not in result

    def test_personal_float_value(self, tmp_path: Path) -> None:
        project = tmp_path / "proj"
        project.mkdir()
        personal = _write(
            tmp_path / "p.toml",
            "[architectanalyst-c]\nmax_instability = 0.6\n",
        )

        result = load_toml_section(project, "architectanalyst-c", personal_config_path=personal)

        assert result["max_instability"] == pytest.approx(0.6)
