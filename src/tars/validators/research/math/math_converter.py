from __future__ import annotations

from pathlib import Path

from tars.validators.base import BaseValidator
from tars.validators.result import ValidationResult


class MathConverter(BaseValidator):
    """Convert extracted math into canonical representations.

    This validator skeleton is intended to transform parsed formulas into forms
    suitable for symbolic and numeric verification workflows.
    """

    name = "math_converter"
    artifact_type = "research-paper"

    def validate(self, artifact_path: Path) -> ValidationResult:
        """Validate/convert math representation for downstream validators."""
        raise NotImplementedError("MathConverter is a skeleton and has no logic yet.")
