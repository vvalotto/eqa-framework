from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

from eqa_framework.config_editor.personal_config import PersonalConfig


def _make_config(tmp_path: Path, content: str = "") -> Path:
    config_file = tmp_path / "config.toml"
    if content:
        config_file.write_text(content, encoding="utf-8")
    return config_file


class TestLoad:
    def test_returns_empty_dict_when_file_does_not_exist(self, tmp_path: Path) -> None:
        cfg = PersonalConfig(tmp_path / "nonexistent.toml")
        assert cfg.load() == {}

    def test_loads_existing_file(self, tmp_path: Path) -> None:
        config_file = _make_config(
            tmp_path,
            "[codeguard-c]\nmax_cyclomatic_complexity = 8\n",
        )
        cfg = PersonalConfig(config_file)
        data = cfg.load()
        assert data == {"codeguard-c": {"max_cyclomatic_complexity": 8}}

    def test_loads_multiple_agents(self, tmp_path: Path) -> None:
        config_file = _make_config(
            tmp_path,
            "[codeguard-c]\nmax_cyclomatic_complexity = 8\n\n[architectanalyst-c]\nmax_instability = 0.6\n",
        )
        cfg = PersonalConfig(config_file)
        data = cfg.load()
        assert data["codeguard-c"] == {"max_cyclomatic_complexity": 8}
        assert data["architectanalyst-c"] == {"max_instability": pytest.approx(0.6)}


class TestSet:
    def test_set_new_agent_and_key(self, tmp_path: Path) -> None:
        cfg = PersonalConfig(tmp_path / "config.toml")
        cfg.load()
        cfg.set("codeguard-c", "max_cyclomatic_complexity", 10)
        assert cfg._data == {"codeguard-c": {"max_cyclomatic_complexity": 10}}

    def test_set_existing_key_overwrites(self, tmp_path: Path) -> None:
        config_file = _make_config(tmp_path, "[codeguard-c]\nmax_cyclomatic_complexity = 8\n")
        cfg = PersonalConfig(config_file)
        cfg.load()
        cfg.set("codeguard-c", "max_cyclomatic_complexity", 15)
        assert cfg._data["codeguard-c"]["max_cyclomatic_complexity"] == 15

    def test_set_new_key_in_existing_agent(self, tmp_path: Path) -> None:
        config_file = _make_config(tmp_path, "[codeguard-c]\nmax_cyclomatic_complexity = 8\n")
        cfg = PersonalConfig(config_file)
        cfg.load()
        cfg.set("codeguard-c", "max_function_length", 50)
        assert cfg._data["codeguard-c"]["max_function_length"] == 50
        assert cfg._data["codeguard-c"]["max_cyclomatic_complexity"] == 8


class TestDelete:
    def test_delete_existing_key(self, tmp_path: Path) -> None:
        config_file = _make_config(
            tmp_path,
            "[codeguard-c]\nmax_cyclomatic_complexity = 8\nmax_function_length = 50\n",
        )
        cfg = PersonalConfig(config_file)
        cfg.load()
        cfg.delete("codeguard-c", "max_cyclomatic_complexity")
        assert "max_cyclomatic_complexity" not in cfg._data["codeguard-c"]
        assert cfg._data["codeguard-c"]["max_function_length"] == 50

    def test_delete_last_key_removes_agent_section(self, tmp_path: Path) -> None:
        config_file = _make_config(tmp_path, "[codeguard-c]\nmax_cyclomatic_complexity = 8\n")
        cfg = PersonalConfig(config_file)
        cfg.load()
        cfg.delete("codeguard-c", "max_cyclomatic_complexity")
        assert "codeguard-c" not in cfg._data

    def test_delete_nonexistent_key_is_noop(self, tmp_path: Path) -> None:
        config_file = _make_config(tmp_path, "[codeguard-c]\nmax_cyclomatic_complexity = 8\n")
        cfg = PersonalConfig(config_file)
        cfg.load()
        cfg.delete("codeguard-c", "does_not_exist")
        assert cfg._data == {"codeguard-c": {"max_cyclomatic_complexity": 8}}

    def test_delete_nonexistent_agent_is_noop(self, tmp_path: Path) -> None:
        cfg = PersonalConfig(tmp_path / "config.toml")
        cfg.load()
        cfg.delete("codeguard-c", "max_cyclomatic_complexity")
        assert cfg._data == {}


class TestSave:
    def test_save_creates_directory_if_missing(self, tmp_path: Path) -> None:
        config_file = tmp_path / "nested" / "dir" / "config.toml"
        cfg = PersonalConfig(config_file)
        cfg.load()
        cfg.set("codeguard-c", "max_cyclomatic_complexity", 8)
        cfg.save()
        assert config_file.exists()

    def test_save_writes_valid_toml(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        cfg = PersonalConfig(config_file)
        cfg.load()
        cfg.set("codeguard-c", "max_cyclomatic_complexity", 8)
        cfg.save()
        data = tomllib.loads(config_file.read_text(encoding="utf-8"))
        assert data == {"codeguard-c": {"max_cyclomatic_complexity": 8}}

    def test_save_roundtrip(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        cfg = PersonalConfig(config_file)
        cfg.load()
        cfg.set("codeguard-c", "max_cyclomatic_complexity", 8)
        cfg.set("architectanalyst-c", "max_instability", 0.6)
        cfg.save()

        cfg2 = PersonalConfig(config_file)
        data = cfg2.load()
        assert data["codeguard-c"] == {"max_cyclomatic_complexity": 8}
        assert data["architectanalyst-c"]["max_instability"] == pytest.approx(0.6)

    def test_save_preserves_other_keys(self, tmp_path: Path) -> None:
        config_file = _make_config(
            tmp_path,
            "[codeguard-c]\nmax_cyclomatic_complexity = 8\nmax_function_length = 50\n",
        )
        cfg = PersonalConfig(config_file)
        cfg.load()
        cfg.set("codeguard-c", "max_cyclomatic_complexity", 12)
        cfg.save()

        data = tomllib.loads(config_file.read_text(encoding="utf-8"))
        assert data["codeguard-c"]["max_cyclomatic_complexity"] == 12
        assert data["codeguard-c"]["max_function_length"] == 50
