from __future__ import annotations

import fnmatch
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from eqa_framework.codeguard_c.config import CodeGuardConfig
from eqa_framework.shared.config import ExecutionContext
from eqa_framework.shared.reporting import Finding, Severity
from eqa_framework.shared.verifiable import Verifiable

# MISRA C:2012 mandatory rules implemented by cppcheck's addon.
# Source: MISRA C:2012 standard + cppcheck addon rule list.
# Rules not in this set are treated as Required (WARNING) or Advisory.
_MISRA_MANDATORY_RULES: frozenset[str] = frozenset(
    {
        "1.2",
        "2.2",
        "5.2",
        "5.4",
        "5.5",
        "5.6",
        "5.7",
        "5.8",
        "5.9",
        "6.1",
        "6.2",
        "7.1",
        "7.2",
        "7.3",
        "7.4",
        "8.1",
        "8.4",
        "8.5",
        "8.6",
        "8.8",
        "8.9",
        "8.10",
        "8.11",
        "9.3",
        "9.4",
        "9.5",
        "11.6",
        "11.7",
        "11.8",
        "11.9",
        "13.6",
        "14.1",
        "15.2",
        "15.3",
        "15.4",
        "15.5",
        "16.7",
        "17.3",
        "17.6",
        "20.13",
        "21.19",
        "21.20",
        "22.5",
    }
)

# Advisory rules in MISRA C:2012 (implemented by cppcheck addon).
# Everything not Mandatory and not Advisory is Required.
_MISRA_ADVISORY_RULES: frozenset[str] = frozenset(
    {
        "2.3",
        "2.4",
        "2.5",
        "2.7",
        "4.1",
        "4.2",
        "12.1",
        "12.3",
        "12.4",
        "15.1",
        "17.8",
        "18.4",
        "18.5",
        "20.1",
    }
)

# cppcheck IDs to skip (noisy meta-messages, not real defects)
_SKIP_IDS: frozenset[str] = frozenset(
    {"missingIncludeSystem", "checkersReport", "tooManyConfigs", "unusedFunction"}
)

_CPPCHECK_SEVERITY_MAP: dict[str, Severity] = {
    "error": Severity.ERROR,
    "warning": Severity.WARNING,
    "style": Severity.WARNING,
    "portability": Severity.WARNING,
    "performance": Severity.INFO,
    "information": Severity.INFO,
}

# Matches "Checking /path/to/file.c ..." lines cppcheck injects into XML stderr
_CHECKING_LINE = re.compile(r"^\s*Checking .*\.\.\.\s*$")


def _is_excluded(path: Path, patterns: list[str]) -> bool:
    name = path.name
    parts = path.parts
    for pattern in patterns:
        stripped = pattern.rstrip("/")
        if pattern.endswith("/"):
            if stripped in parts:
                return True
        elif fnmatch.fnmatch(name, pattern):
            return True
    return False


def _run_cppcheck(files: list[Path]) -> str:
    result = subprocess.run(
        [
            "cppcheck",
            "--xml",
            "--xml-version=2",
            "--addon=misra",
            "--enable=warning,style,information",
            "--suppress=missingIncludeSystem",
            "--suppress=checkersReport",
            *[str(f) for f in files],
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    # cppcheck writes XML to stderr; stdout has the "Checking ..." progress lines
    return result.stderr


def _clean_xml(raw: str) -> str:
    """Remove non-XML 'Checking <file>...' lines cppcheck injects into XML output."""
    lines = [line for line in raw.splitlines() if not _CHECKING_LINE.match(line)]
    return "\n".join(lines)


def _misra_rule_from_id(error_id: str) -> str | None:
    """Extract '8.4' from 'misra-c2012-8.4', or None if not a MISRA id."""
    prefix = "misra-c2012-"
    if error_id.startswith(prefix):
        return error_id[len(prefix) :]
    return None


def _severity_for_misra(rule: str, config: CodeGuardConfig) -> Severity | None:
    if rule in _MISRA_MANDATORY_RULES:
        return Severity.CRITICAL if config.misra_mandatory else None
    if rule in _MISRA_ADVISORY_RULES:
        return Severity.INFO if config.misra_advisory else None
    # Required
    return Severity.WARNING if config.misra_required else None


class MisraCheck(Verifiable):
    """Verifica violaciones MISRA-C 2012 via cppcheck + addon misra."""

    def __init__(self, config: CodeGuardConfig) -> None:
        self._config = config

    @property
    def name(self) -> str:
        return "misra"

    @property
    def estimated_seconds(self) -> int:
        return 8

    def run(self, context: ExecutionContext) -> list[Finding]:
        files = [
            f for f in context.target_files if not _is_excluded(f, self._config.exclude_patterns)
        ]
        if not files:
            return []

        raw_xml = _run_cppcheck(files)
        return self._parse(_clean_xml(raw_xml))

    def _parse(self, xml_str: str) -> list[Finding]:
        if not xml_str.strip():
            return []
        try:
            root = ET.fromstring(xml_str)
        except ET.ParseError:
            return []

        findings: list[Finding] = []
        for error in root.iter("error"):
            error_id = error.get("id", "")
            if error_id in _SKIP_IDS:
                continue

            location = error.find("location")
            if location is None:
                continue
            file_path = Path(location.get("file", ""))
            line = int(location.get("line", "0"))
            msg = error.get("msg", "")

            misra_rule = _misra_rule_from_id(error_id)
            if misra_rule is not None:
                severity = _severity_for_misra(misra_rule, self._config)
                if severity is None:
                    continue
                findings.append(
                    Finding(
                        severity=severity,
                        rule=error_id,
                        message=msg,
                        file=file_path,
                        line=line,
                        tool="cppcheck",
                    )
                )
            else:
                cppcheck_sev = error.get("severity", "")
                severity = _CPPCHECK_SEVERITY_MAP.get(cppcheck_sev)
                if severity is None:
                    continue
                findings.append(
                    Finding(
                        severity=severity,
                        rule=error_id,
                        message=msg,
                        file=file_path,
                        line=line,
                        tool="cppcheck",
                    )
                )

        return findings
