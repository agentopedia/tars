from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .result import ValidationResult


@dataclass
class ValidationIssue:
    code: str
    message: str
    path: str | None = None
    line: int | None = None
    severity: str = "error"


class Validator(Protocol):
    """Protocol for deterministic artifact validators."""

    name: str

    def validate(self, artifact_path: Path) -> ValidationResult:
        ...
