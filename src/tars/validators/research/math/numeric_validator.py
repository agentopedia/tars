from __future__ import annotations

from pathlib import Path

from tars.validators.base import BaseValidator
from tars.validators.result import ValidationResult


class NumericValidator(BaseValidator):
    """Numerically validate equations and claims through deterministic checks.

    This validator skeleton will later execute bounded numeric consistency tests
    for mathematical expressions derived from the paper.
    """

    name = "numeric_validator"
    artifact_type = "research-paper"

    def validate(self, artifact_path: Path) -> ValidationResult:
        """Run numeric validation checks on math content."""
        raise NotImplementedError("NumericValidator is a skeleton and has no logic yet.")
