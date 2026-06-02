from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from eqa_framework.codeguard_c.checks.security_check import SecurityCheck, _is_excluded
from eqa_framework.codeguard_c.config import CodeGuardConfig
from eqa_framework.shared.config import ExecutionContext
from eqa_framework.shared.reporting import Severity

# Real flawfinder --dataonly --csv output:
#   gets   → level 5 (ERROR)
#   strcpy → level 4 (ERROR)
#   sprintf→ level 4 (ERROR)
#   char[] → level 2 (WARNING)
_FLAWFINDER_CSV = """\
File,Line,Column,DefaultLevel,Level,Category,Name,Warning,Suggestion,Note,CWEs,Context,Fingerprint,ToolVersion,RuleId,HelpUri
/src/module.c,6,5,5,5,buffer,gets,"Does not check for buffer overflows (CWE-120, CWE-20).",Use fgets() instead.,,"CWE-120, CWE-20",    gets(buf);,abc123,2.0.20,FF1014,https://cwe.mitre.org/data/definitions/120.html
/src/module.c,7,5,4,4,buffer,strcpy,Does not check for buffer overflows when copying to destination [MS-banned] (CWE-120).,"Consider using snprintf, strcpy_s, or strlcpy (warning: strncpy easily misused).",,CWE-120,"    strcpy(buf, input);",def456,2.0.20,FF1001,https://cwe.mitre.org/data/definitions/120.html
/src/module.c,8,5,4,4,format,sprintf,Potential format string problem (CWE-134).,Make format string constant.,,CWE-134,"    sprintf(buf, input);",ghi789,2.0.20,FF1015,https://cwe.mitre.org/data/definitions/134.html
/src/module.c,5,5,2,2,buffer,char,"Statically-sized arrays can be improperly restricted.",Perform bounds checking.,,CWE-119,    char buf[64];,jkl012,2.0.20,FF1013,https://cwe.mitre.org/data/definitions/119.html
"""

_CONFIG = CodeGuardConfig()


@pytest.fixture()
def ctx(tmp_path: Path) -> ExecutionContext:
    f = tmp_path / "module.c"
    f.touch()
    return ExecutionContext(project_root=tmp_path, target_files=[f])


class TestSecurityCheckParse:
    def _check(self) -> SecurityCheck:
        return SecurityCheck(_CONFIG)

    def test_error_for_level_5(self, ctx: ExecutionContext) -> None:
        with patch(
            "eqa_framework.codeguard_c.checks.security_check._run_flawfinder",
            return_value=_FLAWFINDER_CSV,
        ):
            findings = self._check().run(ctx)
        gets_f = next(f for f in findings if f.rule == "FF1014")
        assert gets_f.severity == Severity.ERROR
        assert "gets" in gets_f.message
        assert gets_f.line == 6

    def test_error_for_level_4(self, ctx: ExecutionContext) -> None:
        with patch(
            "eqa_framework.codeguard_c.checks.security_check._run_flawfinder",
            return_value=_FLAWFINDER_CSV,
        ):
            findings = self._check().run(ctx)
        strcpy_f = next(f for f in findings if f.rule == "FF1001")
        assert strcpy_f.severity == Severity.ERROR
        sprintf_f = next(f for f in findings if f.rule == "FF1015")
        assert sprintf_f.severity == Severity.ERROR

    def test_warning_for_level_2(self, ctx: ExecutionContext) -> None:
        with patch(
            "eqa_framework.codeguard_c.checks.security_check._run_flawfinder",
            return_value=_FLAWFINDER_CSV,
        ):
            findings = self._check().run(ctx)
        char_f = next(f for f in findings if f.rule == "FF1013")
        assert char_f.severity == Severity.WARNING

    def test_total_finding_count(self, ctx: ExecutionContext) -> None:
        with patch(
            "eqa_framework.codeguard_c.checks.security_check._run_flawfinder",
            return_value=_FLAWFINDER_CSV,
        ):
            findings = self._check().run(ctx)
        assert len(findings) == 4

    def test_level_1_is_ignored(self, ctx: ExecutionContext) -> None:
        csv_level1 = (
            "File,Line,Column,DefaultLevel,Level,Category,Name,Warning,"
            "Suggestion,Note,CWEs,Context,Fingerprint,ToolVersion,RuleId,HelpUri\n"
            "/src/module.c,1,1,1,1,misc,random,Some low-risk issue.,,,CWE-000,"
            "foo,abc,2.0.20,FF9999,https://example.com\n"
        )
        with patch(
            "eqa_framework.codeguard_c.checks.security_check._run_flawfinder",
            return_value=csv_level1,
        ):
            findings = self._check().run(ctx)
        assert findings == []

    def test_tool_field_is_flawfinder(self, ctx: ExecutionContext) -> None:
        with patch(
            "eqa_framework.codeguard_c.checks.security_check._run_flawfinder",
            return_value=_FLAWFINDER_CSV,
        ):
            findings = self._check().run(ctx)
        assert all(f.tool == "flawfinder" for f in findings)

    def test_empty_output_returns_no_findings(self, ctx: ExecutionContext) -> None:
        with patch(
            "eqa_framework.codeguard_c.checks.security_check._run_flawfinder",
            return_value="",
        ):
            findings = self._check().run(ctx)
        assert findings == []

    def test_header_only_returns_no_findings(self, ctx: ExecutionContext) -> None:
        header_only = (
            "File,Line,Column,DefaultLevel,Level,Category,Name,Warning,"
            "Suggestion,Note,CWEs,Context,Fingerprint,ToolVersion,RuleId,HelpUri\n"
        )
        with patch(
            "eqa_framework.codeguard_c.checks.security_check._run_flawfinder",
            return_value=header_only,
        ):
            findings = self._check().run(ctx)
        assert findings == []


class TestExcludePatterns:
    def test_directory_pattern_excludes_file(self) -> None:
        assert _is_excluded(Path("/project/build/module.c"), ["build/"])

    def test_glob_pattern_excludes_matching_file(self) -> None:
        assert _is_excluded(Path("/project/src/proto.pb.c"), ["*.pb.c"])

    def test_no_patterns_excludes_nothing(self) -> None:
        assert not _is_excluded(Path("/project/src/module.c"), [])


class TestExcludePatternsIntegration:
    def test_excluded_files_not_passed_to_flawfinder(self, tmp_path: Path) -> None:
        keep = tmp_path / "src" / "module.c"
        keep.parent.mkdir()
        keep.touch()
        exclude = tmp_path / "build" / "generated.c"
        exclude.parent.mkdir()
        exclude.touch()

        ctx = ExecutionContext(
            project_root=tmp_path,
            target_files=[keep, exclude],
        )
        config = CodeGuardConfig(exclude_patterns=["build/"])

        with patch(
            "eqa_framework.codeguard_c.checks.security_check._run_flawfinder",
            return_value="",
        ) as mock_ff:
            SecurityCheck(config).run(ctx)

        called_files = mock_ff.call_args[0][0]
        assert keep in called_files
        assert exclude not in called_files

    def test_all_files_excluded_skips_flawfinder(self, tmp_path: Path) -> None:
        f = tmp_path / "build" / "gen.c"
        f.parent.mkdir()
        f.touch()
        ctx = ExecutionContext(project_root=tmp_path, target_files=[f])
        config = CodeGuardConfig(exclude_patterns=["build/"])

        with patch("eqa_framework.codeguard_c.checks.security_check._run_flawfinder") as mock_ff:
            findings = SecurityCheck(config).run(ctx)

        mock_ff.assert_not_called()
        assert findings == []
