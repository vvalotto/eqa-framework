from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from eqa_framework.codeguard_c.checks.misra_check import (
    MisraCheck,
    _clean_xml,
    _is_excluded,
    _misra_rule_from_id,
)
from eqa_framework.codeguard_c.config import CodeGuardConfig
from eqa_framework.shared.config import ExecutionContext
from eqa_framework.shared.reporting import Severity

# Real cppcheck XML (stderr) with "Checking..." lines removed:
#   nullPointer (error) → ERROR
#   uninitvar   (error) → ERROR
#   misra-c2012-11.9 (mandatory style) → CRITICAL
#   misra-c2012-17.7 (required style)  → WARNING  (×2)
#   misra-c2012-21.6 (required style)  → WARNING  (×2)
_CPPCHECK_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<results version="2">
    <cppcheck version="2.20.0"/>
    <errors>
        <error id="nullPointer" severity="error" msg="Null pointer dereference: p" verbose="Null pointer dereference: p" cwe="476" file0="/src/module.c">
            <location file="/src/module.c" line="8" column="19"/>
        </error>
        <error id="uninitvar" severity="error" msg="Uninitialized variable: x" verbose="Uninitialized variable: x" cwe="457" file0="/src/module.c">
            <location file="/src/module.c" line="7" column="18"/>
        </error>
        <error id="misra-c2012-11.9" severity="style" msg="misra violation" verbose="misra violation" file0="/src/module.c">
            <location file="/src/module.c" line="6" column="12"/>
        </error>
        <error id="misra-c2012-17.7" severity="style" msg="misra violation" verbose="misra violation" file0="/src/module.c">
            <location file="/src/module.c" line="7" column="11"/>
        </error>
        <error id="misra-c2012-21.6" severity="style" msg="misra violation" verbose="misra violation" file0="/src/module.c">
            <location file="/src/module.c" line="8" column="11"/>
        </error>
    </errors>
</results>
"""

_CONFIG = CodeGuardConfig()


@pytest.fixture()
def ctx(tmp_path: Path) -> ExecutionContext:
    f = tmp_path / "module.c"
    f.touch()
    return ExecutionContext(project_root=tmp_path, target_files=[f])


class TestMisraCheckParse:
    def _check(self, config: CodeGuardConfig = _CONFIG) -> MisraCheck:
        return MisraCheck(config)

    def test_null_pointer_is_error(self, ctx: ExecutionContext) -> None:
        with patch(
            "eqa_framework.codeguard_c.checks.misra_check._run_cppcheck",
            return_value=_CPPCHECK_XML,
        ):
            findings = self._check().run(ctx)
        f = next(x for x in findings if x.rule == "nullPointer")
        assert f.severity == Severity.ERROR
        assert f.line == 8
        assert f.tool == "cppcheck"

    def test_uninitvar_is_error(self, ctx: ExecutionContext) -> None:
        with patch(
            "eqa_framework.codeguard_c.checks.misra_check._run_cppcheck",
            return_value=_CPPCHECK_XML,
        ):
            findings = self._check().run(ctx)
        f = next(x for x in findings if x.rule == "uninitvar")
        assert f.severity == Severity.ERROR

    def test_misra_mandatory_rule_is_critical(self, ctx: ExecutionContext) -> None:
        with patch(
            "eqa_framework.codeguard_c.checks.misra_check._run_cppcheck",
            return_value=_CPPCHECK_XML,
        ):
            findings = self._check().run(ctx)
        # rule 11.9 is Mandatory
        f = next(x for x in findings if x.rule == "misra-c2012-11.9")
        assert f.severity == Severity.CRITICAL

    def test_misra_required_rule_is_warning(self, ctx: ExecutionContext) -> None:
        with patch(
            "eqa_framework.codeguard_c.checks.misra_check._run_cppcheck",
            return_value=_CPPCHECK_XML,
        ):
            findings = self._check().run(ctx)
        # rules 17.7 and 21.6 are Required
        required = [x for x in findings if x.rule in ("misra-c2012-17.7", "misra-c2012-21.6")]
        assert all(f.severity == Severity.WARNING for f in required)

    def test_mandatory_suppressed_when_config_off(self, ctx: ExecutionContext) -> None:
        config = CodeGuardConfig(misra_mandatory=False)
        with patch(
            "eqa_framework.codeguard_c.checks.misra_check._run_cppcheck",
            return_value=_CPPCHECK_XML,
        ):
            findings = self._check(config).run(ctx)
        assert all(f.severity != Severity.CRITICAL for f in findings)

    def test_required_suppressed_when_config_off(self, ctx: ExecutionContext) -> None:
        config = CodeGuardConfig(misra_required=False)
        with patch(
            "eqa_framework.codeguard_c.checks.misra_check._run_cppcheck",
            return_value=_CPPCHECK_XML,
        ):
            findings = self._check(config).run(ctx)
        rules = {f.rule for f in findings}
        assert "misra-c2012-17.7" not in rules
        assert "misra-c2012-21.6" not in rules

    def test_empty_xml_returns_no_findings(self, ctx: ExecutionContext) -> None:
        with patch("eqa_framework.codeguard_c.checks.misra_check._run_cppcheck", return_value=""):
            assert self._check().run(ctx) == []

    def test_invalid_xml_returns_no_findings(self, ctx: ExecutionContext) -> None:
        with patch(
            "eqa_framework.codeguard_c.checks.misra_check._run_cppcheck",
            return_value="not xml at all",
        ):
            assert self._check().run(ctx) == []

    def test_skip_ids_are_ignored(self, ctx: ExecutionContext) -> None:
        xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<results version="2"><cppcheck version="2.20.0"/><errors>
<error id="checkersReport" severity="information" msg="Active checkers: 268/386"><location file="/src/module.c" line="1"/></error>
<error id="missingIncludeSystem" severity="information" msg="Include file not found"><location file="/src/module.c" line="1"/></error>
</errors></results>"""
        with patch("eqa_framework.codeguard_c.checks.misra_check._run_cppcheck", return_value=xml):
            assert self._check().run(ctx) == []


class TestCleanXml:
    def test_removes_checking_lines(self) -> None:
        raw = "<?xml?>\nChecking /path/to/file.c ...\n<results/>"
        assert "Checking" not in _clean_xml(raw)

    def test_preserves_xml_content(self) -> None:
        raw = "<?xml?>\n<results version='2'><errors/></results>"
        assert _clean_xml(raw) == raw


class TestMisraRuleFromId:
    def test_extracts_rule_number(self) -> None:
        assert _misra_rule_from_id("misra-c2012-8.4") == "8.4"

    def test_returns_none_for_non_misra(self) -> None:
        assert _misra_rule_from_id("nullPointer") is None

    def test_returns_none_for_empty(self) -> None:
        assert _misra_rule_from_id("") is None


class TestExcludePatterns:
    def test_directory_pattern_excludes_file(self) -> None:
        assert _is_excluded(Path("/project/build/module.c"), ["build/"])

    def test_glob_pattern_excludes_file(self) -> None:
        assert _is_excluded(Path("/project/src/proto.pb.c"), ["*.pb.c"])

    def test_no_patterns_excludes_nothing(self) -> None:
        assert not _is_excluded(Path("/project/src/module.c"), [])


class TestExcludeIntegration:
    def test_all_files_excluded_skips_cppcheck(self, tmp_path: Path) -> None:
        f = tmp_path / "build" / "gen.c"
        f.parent.mkdir()
        f.touch()
        ctx = ExecutionContext(project_root=tmp_path, target_files=[f])
        config = CodeGuardConfig(exclude_patterns=["build/"])

        with patch("eqa_framework.codeguard_c.checks.misra_check._run_cppcheck") as mock_cpp:
            findings = MisraCheck(config).run(ctx)

        mock_cpp.assert_not_called()
        assert findings == []
