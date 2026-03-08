from __future__ import annotations

from pathlib import Path
from typing import Any

from tars.validators.base import BaseValidator
from tars.validators.result import ValidationResult


class SymbolicValidator(BaseValidator):
    """Symbolically validate equation equivalence with SymPy.

    Core check is based on `sympy.simplify(lhs - rhs)` and zero detection.
    """

    name = "symbolic_validator"
    artifact_type = "research-paper"

    @staticmethod
    def _is_zero_expr(expr: Any, sp_module: Any) -> bool:
        if expr == 0:
            return True

        is_zero = getattr(expr, "is_zero", None)
        if is_zero is True:
            return True

        if isinstance(expr, sp_module.MatrixBase):
            zeros = sp_module.zeros(*expr.shape)
            return bool(expr.equals(zeros))

        return False

    def validate_equivalence(self, lhs_sympy: Any, rhs_sympy: Any) -> ValidationResult:
        """Validate whether lhs and rhs are mathematically equivalent."""
        try:
            import sympy as sp  # type: ignore
        except Exception as exc:
            return ValidationResult(
                name=self.name,
                passed=False,
                errors=[f"SymPy is not available: {exc}"],
                metadata={"lhs": str(lhs_sympy), "rhs": str(rhs_sympy)},
            )

        try:
            diff = sp.simplify(lhs_sympy - rhs_sympy)
            passed = self._is_zero_expr(diff, sp)
            return ValidationResult(
                name=self.name,
                passed=passed,
                errors=[] if passed else ["Expressions are not mathematically equivalent"],
                metadata={
                    "lhs": str(lhs_sympy),
                    "rhs": str(rhs_sympy),
                    "difference": str(diff),
                },
            )
        except Exception as exc:
            return ValidationResult(
                name=self.name,
                passed=False,
                errors=[f"Symbolic validation failed: {exc}"],
                metadata={"lhs": str(lhs_sympy), "rhs": str(rhs_sympy)},
            )

    def validate(self, artifact_path: Path) -> ValidationResult:
        """Path-based validation is not implemented for this validator stage."""
        return ValidationResult(
            name=self.name,
            passed=False,
            errors=[
                "Path-based symbolic validation is not implemented. "
                "Use validate_equivalence(lhs_sympy, rhs_sympy)."
            ],
            metadata={"artifact_path": str(artifact_path)},
        )
