from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

import tomli_w

_CONFIG_PATH = Path.home() / ".config" / "eqa" / "config.toml"


class PersonalConfig:
    def __init__(self, config_path: Path = _CONFIG_PATH) -> None:
        self._path = config_path
        self._data: dict[str, dict[str, Any]] = {}

    def load(self) -> dict[str, dict[str, Any]]:
        if not self._path.exists():
            self._data = {}
            return self._data
        raw = tomllib.loads(self._path.read_text(encoding="utf-8"))
        self._data = {k: dict(v) for k, v in raw.items() if isinstance(v, dict)}
        return self._data

    def set(self, agent: str, key: str, value: Any) -> None:
        if agent not in self._data:
            self._data[agent] = {}
        self._data[agent][key] = value

    def delete(self, agent: str, key: str) -> None:
        if agent in self._data and key in self._data[agent]:
            del self._data[agent][key]
            if not self._data[agent]:
                del self._data[agent]

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(tomli_w.dumps(self._data), encoding="utf-8")
