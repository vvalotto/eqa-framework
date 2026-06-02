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
        result = load_toml_section(tmp_project, "codeguard-c")
        assert result == {"max_cyclomatic_complexity": 10}

    def test_returns_empty_dict_when_section_missing(self, tmp_project: Path) -> None:
        (tmp_project / "pyproject.toml").write_text("[tool.other]\nfoo = 1\n", encoding="utf-8")
        result = load_toml_section(tmp_project, "codeguard-c")
        assert result == {}

    def test_returns_empty_dict_when_tool_table_missing(self, tmp_project: Path) -> None:
        (tmp_project / "pyproject.toml").write_text("[project]\nname = 'foo'\n", encoding="utf-8")
        result = load_toml_section(tmp_project, "codeguard-c")
        assert result == {}

    def test_nested_subsection(self, tmp_project: Path) -> None:
        toml = "[tool.codeguard-c]\nmax_function_lines = 50\n\n[tool.codeguard-c.checks]\nmisra_mandatory = true\n"
        (tmp_project / "pyproject.toml").write_text(toml, encoding="utf-8")
        result = load_toml_section(tmp_project, "codeguard-c")
        assert result["max_function_lines"] == 50
        assert result["checks"] == {"misra_mandatory": True}


class TestLoadTomlSectionFallback:
    def test_fallback_to_embedded_qa_toml(self, tmp_project: Path) -> None:
        (tmp_project / ".embedded-qa.toml").write_text(
            "[tool.codeguard-c]\nmax_function_lines = 80\n",
            encoding="utf-8",
        )
        result = load_toml_section(tmp_project, "codeguard-c")
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
        result = load_toml_section(tmp_project, "codeguard-c")
        assert result["max_function_lines"] == 50

    def test_returns_empty_dict_when_no_config_file(self, tmp_project: Path) -> None:
        result = load_toml_section(tmp_project, "codeguard-c")
        assert result == {}

    def test_fallback_section_missing(self, tmp_project: Path) -> None:
        (tmp_project / ".embedded-qa.toml").write_text("[tool.other]\nfoo = 1\n", encoding="utf-8")
        result = load_toml_section(tmp_project, "codeguard-c")
        assert result == {}
