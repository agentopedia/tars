from __future__ import annotations

from pathlib import Path
from typing import Any

from tars.validators.base import BaseValidator
from tars.validators.result import ValidationResult


class DimensionalValidator(BaseValidator):
    """Validate dimensional consistency of unit expressions using Pint."""

    name = "dimensional_validator"
    artifact_type = "research-paper"

    def __init__(self) -> None:
        self._ureg = None

    def _get_ureg(self):
        if self._ureg is None:
            import pint  # type: ignore

            self._ureg = pint.UnitRegistry()
        return self._ureg

    def validate_units(self, lhs_expr: str, rhs_expr: str) -> ValidationResult:
        """Validate that both unit expressions are dimensionally consistent.

        Parameters are Pint-parsable expressions such as:
        - ``meter / second``
        - ``newton * meter``
        - ``kilogram * meter / second**2``
        """
        try:
            ureg = self._get_ureg()
        except Exception as exc:
            return ValidationResult(
                name=self.name,
                passed=False,
                status="SKIPPED",
                reason="pint unavailable",
                errors=[f"Pint is not available: {exc}"],
                metadata={"lhs": lhs_expr, "rhs": rhs_expr},
            )

        try:
            lhs = ureg.parse_expression(lhs_expr)
            rhs = ureg.parse_expression(rhs_expr)
        except Exception as exc:
            return ValidationResult(
                name=self.name,
                passed=False,
                status="SKIPPED",
                reason="conversion failure",
                errors=[f"Unit parsing failed: {exc}"],
                metadata={"lhs": lhs_expr, "rhs": rhs_expr},
            )

        try:
            lhs_compatible = lhs.is_compatible_with(rhs)
        except Exception as exc:
            return ValidationResult(
                name=self.name,
                passed=False,
                status="FAIL",
                reason="invalid unit math",
                errors=[f"Invalid unit math detected: {exc}"],
                metadata={"lhs": lhs_expr, "rhs": rhs_expr},
            )

        if lhs_compatible:
            return ValidationResult(
                name=self.name,
                passed=True,
                status="PASS",
                errors=[],
                metadata={
                    "lhs": lhs_expr,
                    "rhs": rhs_expr,
                    "lhs_dimensionality": str(getattr(lhs, "dimensionality", "")),
                    "rhs_dimensionality": str(getattr(rhs, "dimensionality", "")),
                },
            )

        return ValidationResult(
            name=self.name,
            passed=False,
            status="FAIL",
            reason="unit mismatch",
            errors=["Unit mismatch: expressions are not dimensionally consistent"],
            metadata={
                "lhs": lhs_expr,
                "rhs": rhs_expr,
                "lhs_dimensionality": str(getattr(lhs, "dimensionality", "")),
                "rhs_dimensionality": str(getattr(rhs, "dimensionality", "")),
            },
        )

    def validate_equivalence(self, lhs_unit_expr: Any, rhs_unit_expr: Any) -> ValidationResult:
        """Alias to validate unit equivalence for API parity with other validators."""
        return self.validate_units(str(lhs_unit_expr), str(rhs_unit_expr))

    def validate(self, artifact_path: Path) -> ValidationResult:
        """Path-based validation is not implemented for this validator stage."""
        return ValidationResult(
            name=self.name,
            passed=False,
            status="SKIPPED",
            reason="not implemented",
            errors=[
                "Path-based dimensional validation is not implemented. "
                "Use validate_units(lhs_expr, rhs_expr)."
            ],
            metadata={"artifact_path": str(artifact_path)},
        )
