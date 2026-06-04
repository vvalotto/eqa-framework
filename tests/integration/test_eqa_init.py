from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from eqa_framework.init.agent import main

pytestmark = pytest.mark.integration


class TestNoInteractive:
    def test_creates_pyproject_in_empty_dir(self, tmp_path: Path) -> None:
        result = CliRunner().invoke(main, [str(tmp_path), "--no-interactive"])
        assert result.exit_code == 0
        assert (tmp_path / "pyproject.toml").exists()

    def test_created_file_has_three_sections(self, tmp_path: Path) -> None:
        CliRunner().invoke(main, [str(tmp_path), "--no-interactive"])
        content = (tmp_path / "pyproject.toml").read_text()
        assert "[tool.codeguard-c]" in content
        assert "[tool.designreviewer-c]" in content
        assert "[tool.architectanalyst-c]" in content

    def test_created_file_has_layers_todo(self, tmp_path: Path) -> None:
        CliRunner().invoke(main, [str(tmp_path), "--no-interactive"])
        content = (tmp_path / "pyproject.toml").read_text()
        assert "TODO" in content

    def test_appends_missing_sections_to_existing(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "myproject"\n', encoding="utf-8"
        )
        CliRunner().invoke(main, [str(tmp_path), "--no-interactive"])
        content = (tmp_path / "pyproject.toml").read_text()
        assert "[project]" in content
        assert "[tool.codeguard-c]" in content

    def test_skips_when_all_sections_exist(self, tmp_path: Path) -> None:
        existing = "[tool.codeguard-c]\n" "[tool.designreviewer-c]\n" "[tool.architectanalyst-c]\n"
        (tmp_path / "pyproject.toml").write_text(existing, encoding="utf-8")
        result = CliRunner().invoke(main, [str(tmp_path), "--no-interactive"])
        assert result.exit_code == 0
        assert "Sin cambios" in result.output
        assert (tmp_path / "pyproject.toml").read_text() == existing

    def test_exit_code_zero_always(self, tmp_path: Path) -> None:
        result = CliRunner().invoke(main, [str(tmp_path), "--no-interactive"])
        assert result.exit_code == 0

    def test_src_dir_option_passed_to_scanner(self, tmp_path: Path) -> None:
        firmware = tmp_path / "firmware"
        firmware.mkdir()
        (firmware / "hal").mkdir()
        result = CliRunner().invoke(
            main, [str(tmp_path), "--no-interactive", "--src-dir", "firmware"]
        )
        assert result.exit_code == 0
        assert "hal" in result.output

    def test_default_path_is_current_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        result = CliRunner().invoke(main, ["--no-interactive"])
        assert result.exit_code == 0
        assert (tmp_path / "pyproject.toml").exists()

    def test_output_reports_written_sections(self, tmp_path: Path) -> None:
        result = CliRunner().invoke(main, [str(tmp_path), "--no-interactive"])
        assert "codeguard-c" in result.output
        assert "designreviewer-c" in result.output
        assert "architectanalyst-c" in result.output


class TestGuide:
    def test_guide_exits_zero(self) -> None:
        result = CliRunner().invoke(main, ["--guide"])
        assert result.exit_code == 0

    def test_guide_contains_key_sections(self) -> None:
        result = CliRunner().invoke(main, ["--guide"])
        assert "eqa-init" in result.output
        assert "codeguard-c" in result.output
        assert "pip install" in result.output
