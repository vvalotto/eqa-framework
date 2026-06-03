from __future__ import annotations

from pathlib import Path

import pytest

from eqa_framework.shared.config import load_toml_section


@pytest.fixture()
def tmp_project(tmp_path: Path) -> Path:
    return tmp_path


class TestLoadTomlSectionPyproject:
    def test_returns_section_values(self, tmp_project: Path) -> None:
        (tmp_project / "pyproject.toml").write_text(
            "[tool.codeguard-c]\nmax_cyclomatic_complexity = 10\n",
            encoding="utf-8",
        )
        result = load_toml_section(tmp_project, "codeguard-c", apply_personal=False)
        assert result == {"max_cyclomatic_complexity": 10}

    def test_returns_empty_dict_when_section_missing(self, tmp_project: Path) -> None:
        (tmp_project / "pyproject.toml").write_text("[tool.other]\nfoo = 1\n", encoding="utf-8")
        result = load_toml_section(tmp_project, "codeguard-c", apply_personal=False)
        assert result == {}

    def test_returns_empty_dict_when_tool_table_missing(self, tmp_project: Path) -> None:
        (tmp_project / "pyproject.toml").write_text("[project]\nname = 'foo'\n", encoding="utf-8")
        result = load_toml_section(tmp_project, "codeguard-c", apply_personal=False)
        assert result == {}

    def test_nested_subsection(self, tmp_project: Path) -> None:
        toml = "[tool.codeguard-c]\nmax_function_lines = 50\n\n[tool.codeguard-c.checks]\nmisra_mandatory = true\n"
        (tmp_project / "pyproject.toml").write_text(toml, encoding="utf-8")
        result = load_toml_section(tmp_project, "codeguard-c", apply_personal=False)
        assert result["max_function_lines"] == 50
        assert result["checks"] == {"misra_mandatory": True}


class TestLoadTomlSectionFallback:
    def test_fallback_to_embedded_qa_toml(self, tmp_project: Path) -> None:
        (tmp_project / ".embedded-qa.toml").write_text(
            "[tool.codeguard-c]\nmax_function_lines = 80\n",
            encoding="utf-8",
        )
        result = load_toml_section(tmp_project, "codeguard-c", apply_personal=False)
        assert result == {"max_function_lines": 80}

    def test_pyproject_takes_priority_over_fallback(self, tmp_project: Path) -> None:
        (tmp_project / "pyproject.toml").write_text(
            "[tool.codeguard-c]\nmax_function_lines = 50\n",
            encoding="utf-8",
        )
        (tmp_project / ".embedded-qa.toml").write_text(
            "[tool.codeguard-c]\nmax_function_lines = 99\n",
            encoding="utf-8",
        )
        result = load_toml_section(tmp_project, "codeguard-c", apply_personal=False)
        assert result["max_function_lines"] == 50

    def test_returns_empty_dict_when_no_config_file(self, tmp_project: Path) -> None:
        result = load_toml_section(tmp_project, "codeguard-c", apply_personal=False)
        assert result == {}

    def test_fallback_section_missing(self, tmp_project: Path) -> None:
        (tmp_project / ".embedded-qa.toml").write_text("[tool.other]\nfoo = 1\n", encoding="utf-8")
        result = load_toml_section(tmp_project, "codeguard-c", apply_personal=False)
        assert result == {}


class TestLoadTomlSectionPersonalMerge:
    def test_personal_key_overrides_project_key(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        (project / "pyproject.toml").write_text(
            "[tool.codeguard-c]\nmax_cyclomatic_complexity = 12\nmax_function_lines = 50\n",
            encoding="utf-8",
        )
        personal_file = tmp_path / "personal.toml"
        personal_file.write_text("[codeguard-c]\nmax_cyclomatic_complexity = 8\n", encoding="utf-8")

        result = load_toml_section(project, "codeguard-c", personal_config_path=personal_file)

        assert result["max_cyclomatic_complexity"] == 8
        assert result["max_function_lines"] == 50

    def test_personal_only_key_added_to_result(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        (project / "pyproject.toml").write_text(
            "[tool.codeguard-c]\nmax_cyclomatic_complexity = 12\n",
            encoding="utf-8",
        )
        personal_file = tmp_path / "personal.toml"
        personal_file.write_text("[codeguard-c]\nmax_instability = 0.6\n", encoding="utf-8")

        result = load_toml_section(project, "codeguard-c", personal_config_path=personal_file)

        assert result["max_cyclomatic_complexity"] == 12
        assert result["max_instability"] == pytest.approx(0.6)

    def test_project_key_preserved_when_not_in_personal(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        (project / "pyproject.toml").write_text(
            "[tool.codeguard-c]\nmax_cyclomatic_complexity = 12\nmax_function_lines = 50\n",
            encoding="utf-8",
        )
        personal_file = tmp_path / "personal.toml"
        personal_file.write_text("[architectanalyst-c]\nmax_instability = 0.6\n", encoding="utf-8")

        result = load_toml_section(project, "codeguard-c", personal_config_path=personal_file)

        assert result == {"max_cyclomatic_complexity": 12, "max_function_lines": 50}

    def test_personal_nonexistent_file_returns_project_config(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        (project / "pyproject.toml").write_text(
            "[tool.codeguard-c]\nmax_cyclomatic_complexity = 12\n",
            encoding="utf-8",
        )
        personal_file = tmp_path / "nonexistent.toml"

        result = load_toml_section(project, "codeguard-c", personal_config_path=personal_file)

        assert result == {"max_cyclomatic_complexity": 12}

    def test_apply_personal_false_ignores_personal_file(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        (project / "pyproject.toml").write_text(
            "[tool.codeguard-c]\nmax_cyclomatic_complexity = 12\n",
            encoding="utf-8",
        )
        personal_file = tmp_path / "personal.toml"
        personal_file.write_text("[codeguard-c]\nmax_cyclomatic_complexity = 5\n", encoding="utf-8")

        result = load_toml_section(
            project, "codeguard-c", apply_personal=False, personal_config_path=personal_file
        )

        assert result == {"max_cyclomatic_complexity": 12}

    def test_empty_project_config_with_personal_keys(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        personal_file = tmp_path / "personal.toml"
        personal_file.write_text("[codeguard-c]\nmax_cyclomatic_complexity = 8\n", encoding="utf-8")

        result = load_toml_section(project, "codeguard-c", personal_config_path=personal_file)

        assert result == {"max_cyclomatic_complexity": 8}
