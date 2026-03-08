from __future__ import annotations

from pathlib import Path

from tars.validators.base import BaseValidator
from tars.validators.result import ValidationResult


class MathValidator(BaseValidator):
    """Top-level math validation orchestrator for research artifacts.

    This validator skeleton will eventually coordinate extraction, conversion,
    symbolic checks, and numeric checks into a single math validation pass.
    """

    name = "math_validator"
    artifact_type = "research-paper"

    def validate(self, artifact_path: Path) -> ValidationResult:
        """Run end-to-end mathematical validation workflow."""
        raise NotImplementedError("MathValidator is a skeleton and has no logic yet.")
