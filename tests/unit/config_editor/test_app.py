from __future__ import annotations

from pathlib import Path

import pytest

from eqa_framework.config_editor.app import _SCHEMA, EqaConfigApp, KeySpec, _fmt, _parse


class TestFmt:
    def test_int(self) -> None:
        assert _fmt(10) == "10"

    def test_float_two_decimals(self) -> None:
        assert _fmt(0.3) == "0.30"

    def test_bool_true(self) -> None:
        assert _fmt(True) == "True"

    def test_str(self) -> None:
        assert _fmt("hello") == "hello"


class TestParse:
    def test_int(self) -> None:
        assert _parse("8", int) == 8

    def test_float(self) -> None:
        assert _parse("0.6", float) == pytest.approx(0.6)

    def test_str(self) -> None:
        assert _parse("mypath", str) == "mypath"

    def test_bool_true_variants(self) -> None:
        for val in ("true", "True", "1", "yes"):
            assert _parse(val, bool) is True

    def test_bool_false_variants(self) -> None:
        for val in ("false", "False", "0", "no"):
            assert _parse(val, bool) is False

    def test_bool_invalid_raises(self) -> None:
        with pytest.raises(ValueError):
            _parse("maybe", bool)

    def test_int_invalid_raises(self) -> None:
        with pytest.raises((ValueError, TypeError)):
            _parse("abc", int)

    def test_float_invalid_raises(self) -> None:
        with pytest.raises((ValueError, TypeError)):
            _parse("abc", float)


class TestSchema:
    def test_schema_has_14_entries(self) -> None:
        assert len(_SCHEMA) == 14

    def test_all_agents_present(self) -> None:
        agents = {s.agent for s in _SCHEMA}
        assert agents == {"codeguard-c", "designreviewer-c", "architectanalyst-c"}

    def test_codeguard_keys(self) -> None:
        keys = {s.key for s in _SCHEMA if s.agent == "codeguard-c"}
        assert keys == {
            "max_cyclomatic_complexity",
            "max_function_lines",
            "misra_mandatory",
            "misra_required",
            "misra_advisory",
        }

    def test_designreviewer_keys(self) -> None:
        keys = {s.key for s in _SCHEMA if s.agent == "designreviewer-c"}
        assert keys == {
            "max_fan_out",
            "max_function_lines",
            "max_parameters",
            "max_nesting_depth",
            "max_cc_critical",
        }

    def test_architectanalyst_keys(self) -> None:
        keys = {s.key for s in _SCHEMA if s.agent == "architectanalyst-c"}
        assert keys == {
            "max_instability",
            "max_distance_warning",
            "max_distance_critical",
            "db_path",
        }

    def test_all_entries_are_keyspec(self) -> None:
        assert all(isinstance(s, KeySpec) for s in _SCHEMA)

    def test_types_are_valid(self) -> None:
        for spec in _SCHEMA:
            assert spec.type_ in (int, float, bool, str)


class TestEqaConfigAppInit:
    def test_init_without_project_config(self, tmp_path: Path) -> None:
        personal = tmp_path / "personal.toml"
        app = EqaConfigApp(project_root=tmp_path, personal_config_path=personal)
        assert app._dirty is False
        assert app._project == {
            "codeguard-c": {},
            "designreviewer-c": {},
            "architectanalyst-c": {},
        }

    def test_init_loads_project_config(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text(
            "[tool.codeguard-c]\nmax_cyclomatic_complexity = 15\n",
            encoding="utf-8",
        )
        personal = tmp_path / "personal.toml"
        app = EqaConfigApp(project_root=tmp_path, personal_config_path=personal)
        assert app._project["codeguard-c"]["max_cyclomatic_complexity"] == 15

    def test_init_loads_personal_config(self, tmp_path: Path) -> None:
        personal = tmp_path / "personal.toml"
        personal.write_text("[codeguard-c]\nmax_cyclomatic_complexity = 8\n", encoding="utf-8")
        app = EqaConfigApp(project_root=tmp_path, personal_config_path=personal)
        assert app._personal._data["codeguard-c"]["max_cyclomatic_complexity"] == 8

    def test_init_does_not_apply_personal_to_project(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text(
            "[tool.codeguard-c]\nmax_cyclomatic_complexity = 12\n",
            encoding="utf-8",
        )
        personal = tmp_path / "personal.toml"
        personal.write_text("[codeguard-c]\nmax_cyclomatic_complexity = 5\n", encoding="utf-8")
        app = EqaConfigApp(project_root=tmp_path, personal_config_path=personal)
        assert app._project["codeguard-c"]["max_cyclomatic_complexity"] == 12
