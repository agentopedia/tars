from __future__ import annotations

from pathlib import Path

from tars.validators.base import BaseValidator
from tars.validators.result import ValidationResult


class MathExtractor(BaseValidator):
    """Extract mathematical expressions from research artifacts.

    This validator skeleton will eventually identify and normalize equations,
    inline formulas, and math blocks from a paper input for downstream checks.
    """

    name = "math_extractor"
    artifact_type = "research-paper"

    def validate(self, artifact_path: Path) -> ValidationResult:
        """Validate/extract math structures from the given artifact path."""
        raise NotImplementedError("MathExtractor is a skeleton and has no logic yet.")
