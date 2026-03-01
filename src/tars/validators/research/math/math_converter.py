from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from tars.validators.base import BaseValidator
from tars.validators.result import ValidationResult

from .math_extractor import MathExtractor


@dataclass
class ConversionError:
    """Structured conversion failure payload."""

    latex: str
    error_type: str
    message: str


@dataclass
class ConversionResult:
    """Structured conversion response for one LaTeX expression."""

    latex: str
    success: bool
    sympy_expr: Any | None = None
    error: ConversionError | None = None


def convert_latex_to_sympy(latex_str: str):
    """Convert LaTeX to a SymPy expression using `latex2sympy2`.

    Returns either a SymPy expression on success, or a `ConversionError` on failure.
    """
    try:
        from latex2sympy2 import latex2sympy  # type: ignore
    except Exception as exc:  # dependency missing or broken install
        return ConversionError(
            latex=latex_str,
            error_type=type(exc).__name__,
            message="latex2sympy2 is not available",
        )

    try:
        return latex2sympy(latex_str)
    except Exception as exc:
        return ConversionError(
            latex=latex_str,
            error_type=type(exc).__name__,
            message=str(exc),
        )


def convert_latex_to_sympy_result(latex_str: str) -> ConversionResult:
    """Always-return structured conversion result wrapper."""
    converted = convert_latex_to_sympy(latex_str)
    if isinstance(converted, ConversionError):
        return ConversionResult(latex=latex_str, success=False, error=converted)
    return ConversionResult(latex=latex_str, success=True, sympy_expr=converted)


class MathConverter(BaseValidator):
    """Convert extracted LaTeX math into SymPy expressions.

    This validator uses `MathExtractor` to collect equations and then attempts
    conversion for each equation side (`lhs`, `rhs`) with `latex2sympy2`.
    """

    name = "math_converter"
    artifact_type = "research-paper"

    def __init__(self) -> None:
        self.extractor = MathExtractor()

    def validate(self, artifact_path: Path) -> ValidationResult:
        """Run extraction + conversion and return structured outcomes."""
        extraction = self.extractor.validate(artifact_path)
        if not extraction.passed:
            return ValidationResult(
                name=self.name,
                passed=False,
                errors=extraction.errors,
                metadata={"artifact_path": str(artifact_path), "conversions": []},
            )

        conversions: list[dict] = []
        errors: list[str] = []
        for equation in extraction.metadata.get("equations", []):
            lhs_result = convert_latex_to_sympy_result(equation["lhs"])
            rhs_result = convert_latex_to_sympy_result(equation["rhs"])

            if not lhs_result.success and lhs_result.error:
                errors.append(
                    f"LHS conversion failed at {equation['source_location']}: "
                    f"{lhs_result.error.message}"
                )
            if not rhs_result.success and rhs_result.error:
                errors.append(
                    f"RHS conversion failed at {equation['source_location']}: "
                    f"{rhs_result.error.message}"
                )

            conversions.append(
                {
                    "source_location": equation["source_location"],
                    "raw": equation["raw"],
                    "lhs": asdict(lhs_result)
                    if not lhs_result.success
                    else {
                        "latex": lhs_result.latex,
                        "success": True,
                        "sympy_expr": str(lhs_result.sympy_expr),
                        "error": None,
                    },
                    "rhs": asdict(rhs_result)
                    if not rhs_result.success
                    else {
                        "latex": rhs_result.latex,
                        "success": True,
                        "sympy_expr": str(rhs_result.sympy_expr),
                        "error": None,
                    },
                }
            )

        return ValidationResult(
            name=self.name,
            passed=not errors,
            errors=errors,
            metadata={
                "artifact_path": str(artifact_path),
                "conversion_count": len(conversions),
                "conversions": conversions,
            },
        )
