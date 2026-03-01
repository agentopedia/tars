from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


@dataclass
class ValidationIssue:
    code: str
    message: str
    path: str | None = None
    line: int | None = None
    severity: str = "error"


@dataclass
class ValidationResult:
    validator_name: str
    passed: bool
    issues: list[ValidationIssue] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class Validator(Protocol):
    """Protocol for deterministic artifact validators."""

    name: str

    def validate(self, artifact_path: Path) -> ValidationResult:
        ...
