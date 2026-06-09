from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class Severity(str, Enum):
    FATAL = "fatal"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class RuleMetadata:
    id: str
    title: str
    requirement_ids: tuple[str, ...]
    severity: Severity


@dataclass(frozen=True)
class ValidationIssue:
    rule_id: str
    requirement_ids: tuple[str, ...]
    severity: Severity
    message: str
    path: str
    manifest: str | None = None
    json_pointer: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "rule_id": self.rule_id,
            "requirement_ids": list(self.requirement_ids),
            "severity": self.severity.value,
            "message": self.message,
            "path": self.path,
        }
        if self.manifest is not None:
            data["manifest"] = self.manifest
        if self.json_pointer is not None:
            data["json_pointer"] = self.json_pointer
        return data


@dataclass(frozen=True)
class Limits:
    max_archive_size: int = 2 * 1024 * 1024 * 1024
    max_uncompressed_size: int = 4 * 1024 * 1024 * 1024
    max_entries: int = 100_000
    max_entry_size: int = 1024 * 1024 * 1024
    max_manifest_size: int = 10 * 1024 * 1024
    max_json_depth: int = 100


@dataclass
class ValidationResult:
    input: Path
    mode: str
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not any(issue.severity in {Severity.FATAL, Severity.ERROR} for issue in self.issues)

    def add(self, issue: ValidationIssue) -> None:
        self.issues.append(issue)

    def extend(self, issues: list[ValidationIssue]) -> None:
        self.issues.extend(issues)

    def summary(self) -> dict[str, int]:
        return {
            severity.value: sum(1 for issue in self.issues if issue.severity == severity)
            for severity in Severity
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "input": str(self.input),
            "mode": self.mode,
            "valid": self.valid,
            "summary": self.summary(),
            "issues": [issue.to_dict() for issue in self.issues],
        }
