from __future__ import annotations

from pathlib import Path

from eqa_framework.init.writer import ConfigWriter, _derive_layers, generate_toml


class TestDeriveLayers:
    def test_empty_returns_empty_dict(self) -> None:
        assert _derive_layers([]) == {}

    def test_single_layer_has_no_deps(self) -> None:
        assert _derive_layers(["platform"]) == {"platform": []}

    def test_two_layers(self) -> None:
        result = _derive_layers(["platform", "hal"])
        assert result == {"platform": [], "hal": ["platform"]}

    def test_three_levels(self) -> None:
        result = _derive_layers(["platform", "hal", "app"])
        assert result == {
            "platform": [],
            "hal": ["platform"],
            "app": ["platform", "hal"],
        }

    def test_preserves_order(self) -> None:
        result = _derive_layers(["a", "b", "c", "d"])
        assert result["d"] == ["a", "b", "c"]


class TestGenerateToml:
    def test_contains_three_sections(self) -> None:
        toml = generate_toml([])
        assert "[tool.codeguard-c]" in toml
        assert "[tool.designreviewer-c]" in toml
        assert "[tool.architectanalyst-c]" in toml

    def test_no_layers_has_todo_comment(self) -> None:
        toml = generate_toml([])
        assert "TODO" in toml
        assert "[tool.designreviewer-c.layers]" in toml

    def test_with_layers_derives_deps(self) -> None:
        toml = generate_toml(["platform", "hal", "app"])
        assert "platform" in toml
        assert '"platform"' in toml
        assert "TODO" not in toml

    def test_with_single_layer(self) -> None:
        toml = generate_toml(["hal"])
        assert "hal" in toml
        assert "TODO" not in toml

    def test_contains_defaults(self) -> None:
        toml = generate_toml([])
        assert "max_cyclomatic_complexity = 10" in toml
        assert "max_instability       = 0.8" in toml
        assert "max_fan_out      = 12" in toml


class TestConfigWriter:
    def test_creates_new_file(self, tmp_path: Path) -> None:
        written = ConfigWriter().write(tmp_path, generate_toml([]))
        assert (tmp_path / "pyproject.toml").exists()
        assert len(written) == 3

    def test_new_file_content_has_three_sections(self, tmp_path: Path) -> None:
        ConfigWriter().write(tmp_path, generate_toml([]))
        content = (tmp_path / "pyproject.toml").read_text()
        assert "[tool.codeguard-c]" in content
        assert "[tool.designreviewer-c]" in content
        assert "[tool.architectanalyst-c]" in content

    def test_appends_to_existing_file(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "myapp"\n', encoding="utf-8")
        ConfigWriter().write(tmp_path, generate_toml([]))
        content = (tmp_path / "pyproject.toml").read_text()
        assert "[project]" in content
        assert "[tool.codeguard-c]" in content

    def test_skips_existing_sections(self, tmp_path: Path) -> None:
        existing = "[tool.codeguard-c]\nmax_cyclomatic_complexity = 5\n"
        (tmp_path / "pyproject.toml").write_text(existing, encoding="utf-8")
        written = ConfigWriter().write(tmp_path, generate_toml([]))
        assert "[tool.codeguard-c]" not in written
        assert "[tool.designreviewer-c]" in written
        assert "[tool.architectanalyst-c]" in written

    def test_skips_all_if_all_exist(self, tmp_path: Path) -> None:
        content = "[tool.codeguard-c]\n[tool.designreviewer-c]\n[tool.architectanalyst-c]\n"
        (tmp_path / "pyproject.toml").write_text(content, encoding="utf-8")
        written = ConfigWriter().write(tmp_path, generate_toml([]))
        assert written == []

    def test_returns_written_section_markers(self, tmp_path: Path) -> None:
        written = ConfigWriter().write(tmp_path, generate_toml([]))
        assert set(written) == {
            "[tool.codeguard-c]",
            "[tool.designreviewer-c]",
            "[tool.architectanalyst-c]",
        }

    def test_existing_file_not_modified_when_all_present(self, tmp_path: Path) -> None:
        content = "[tool.codeguard-c]\n[tool.designreviewer-c]\n[tool.architectanalyst-c]\n"
        (tmp_path / "pyproject.toml").write_text(content, encoding="utf-8")
        ConfigWriter().write(tmp_path, generate_toml([]))
        assert (tmp_path / "pyproject.toml").read_text() == content
