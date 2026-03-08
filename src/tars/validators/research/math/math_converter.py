from __future__ import annotations

from dataclasses import asdict, dataclass
import logging
from pathlib import Path
import re
from typing import Any

from tars.validators.base import BaseValidator
from tars.validators.result import ValidationResult

from .math_extractor import MathExtractor


logger = logging.getLogger(__name__)


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


@dataclass
class EquationConversionResult:
    """Structured conversion response for equation sides."""

    lhs_sympy: Any | None = None
    rhs_sympy: Any | None = None
    error: ConversionError | None = None


def normalize_latex_for_sympy(latex_str: str) -> str:
    """Normalize LaTeX to improve parser compatibility.

    Rules:
    - Strip metadata tags: `\\label{...}`, `\\nonumber`, `\\cite...{...}`
    - Simplify `\\mbox{...}` payload to plain token-like text
    - Standardize differential notation for `d` and `\\partial`
    - Replace apostrophe prime notation with `_prime` suffix
    """
    text = latex_str

    # 1) Strip metadata / citations
    text = re.sub(r"\\label\{[^{}]*\}", "", text)
    text = re.sub(r"\\nonumber\b", "", text)
    text = re.sub(r"\\cite[a-zA-Z*]*\{[^{}]*\}", "", text)

    # 2) Simplify mbox payload
    def _mbox_repl(match: re.Match[str]) -> str:
        payload = match.group(1)
        payload = re.sub(r"\s+", "_", payload.strip())
        payload = re.sub(r"[^A-Za-z0-9_]", "", payload)
        return payload or "mbox_var"

    text = re.sub(r"\\mbox\{([^{}]*)\}", _mbox_repl, text)

    # 3) Standardize differentials
    text = text.replace(r"\mathrm{d}", "d")
    text = text.replace(r"\operatorname{d}", "d")
    text = text.replace(r"\mathrm{\partial}", r"\partial")
    text = re.sub(r"d\s+([A-Za-z])", r"d\1", text)
    text = re.sub(r"\\partial\s+([A-Za-z])", r"\\partial \1", text)
    text = re.sub(r"\\int\s+", r"\\int ", text)

    # 4) Prime notation handling: x' -> x_prime, x'' -> x_prime2
    text = re.sub(r"([A-Za-z])''", r"\1_prime2", text)
    text = re.sub(r"([A-Za-z])'", r"\1_prime", text)

    # cleanup spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


def convert_latex_to_sympy(latex_str: str):
    """Convert LaTeX to a SymPy expression using `latex2sympy2`.

    Returns either a SymPy expression on success, or a `ConversionError` on failure.
    """
    normalized = normalize_latex_for_sympy(latex_str)
    logger.debug("Converting LaTeX to SymPy", extra={"latex": latex_str, "normalized": normalized})

    try:
        from latex2sympy2 import latex2sympy  # type: ignore
    except Exception as exc:  # dependency missing or broken install
        logger.debug("latex2sympy2 unavailable", exc_info=exc)
        return ConversionError(
            latex=latex_str,
            error_type=type(exc).__name__,
            message="latex2sympy2 is not available",
        )

    try:
        return latex2sympy(normalized)
    except Exception as exc:
        logger.debug(
            "LaTeX conversion failed",
            extra={"latex": latex_str, "normalized": normalized, "error": str(exc)},
        )
        return ConversionError(
            latex=latex_str,
            error_type=type(exc).__name__,
            message=str(exc),
        )


def convert_equation(lhs_latex: str, rhs_latex: str) -> EquationConversionResult:
    """Convert equation sides (lhs, rhs) from LaTeX to SymPy.

    Returns SymPy expressions in `lhs_sympy` and `rhs_sympy` on success.
    If either side fails, returns a structured `ConversionError`.
    """
    logger.info("Converting equation", extra={"lhs": lhs_latex, "rhs": rhs_latex})

    lhs = convert_latex_to_sympy(lhs_latex)
    if isinstance(lhs, ConversionError):
        logger.debug("Failed LHS equation conversion", extra={"lhs": lhs_latex, "error": lhs.message})
        return EquationConversionResult(error=lhs)

    rhs = convert_latex_to_sympy(rhs_latex)
    if isinstance(rhs, ConversionError):
        logger.debug("Failed RHS equation conversion", extra={"rhs": rhs_latex, "error": rhs.message})
        return EquationConversionResult(error=rhs)

    logger.info("Equation conversion successful")
    return EquationConversionResult(lhs_sympy=lhs, rhs_sympy=rhs)


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
            eq_result = convert_equation(equation["lhs"], equation["rhs"])

            if eq_result.error:
                errors.append(
                    f"Equation conversion failed at {equation['source_location']}: "
                    f"{eq_result.error.message}"
                )

            conversions.append(
                {
                    "source_location": equation["source_location"],
                    "raw": equation["raw"],
                    "lhs_sympy": None if eq_result.error else str(eq_result.lhs_sympy),
                    "rhs_sympy": None if eq_result.error else str(eq_result.rhs_sympy),
                    "error": asdict(eq_result.error) if eq_result.error else None,
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
