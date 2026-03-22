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
    - Strip metadata tags: `\label{...}`, `\nonumber`, `\cite...{...}`
    - Simplify `\mbox{...}` payload to plain token-like text
    - Standardize differential notation for `d` and `\partial`
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


def _failure_severity(latex: str, source_location: str | None = None) -> str:
    """Classify whether conversion failure is blocking or cosmetic."""
    text = latex.lower()
    source = (source_location or "").lower()
    if any(token in text for token in ["\\frac", "\\int", "\\sum", "=", "\\partial"]) or "equation" in source:
        return "CRITICAL"
    return "MINOR"


def _failure_explanation(error_message: str) -> str:
    msg = error_message.lower()
    if "no viable alternative" in msg or "mismatched" in msg:
        return "The LaTeX parser could not understand this structure; syntax is likely malformed or unsupported."
    if "not available" in msg:
        return "The converter backend is unavailable in this environment."
    if "undefined" in msg or "unknown" in msg:
        return "The expression appears to use macros/operators not recognized by the converter."
    return "This equation uses notation that the current LaTeX-to-SymPy parser could not convert."


def _fix_suggestions(latex: str) -> list[str]:
    suggestions: list[str] = []
    if "\\text{" in latex:
        suggestions.append("Replace \\text{...} blocks with plain symbolic identifiers (e.g., cfl_term).")
    if "\\left" in latex or "\\right" in latex:
        suggestions.append("Try removing \\left/\\right wrappers and use plain parentheses.")
    if "\\mbox" in latex:
        suggestions.append("Replace \\mbox{...} with a single variable-style token.")
    if "\\operatorname" in latex:
        suggestions.append("Rewrite \\operatorname{...} constructs to supported SymPy function names.")
    if "\\" in latex and not suggestions:
        suggestions.append("Try simplifying custom macros and unsupported commands into basic LaTeX math operators.")
    suggestions.append("Ensure integrals/derivatives use standard forms like \\int f(x) dx and \\frac{d}{dx}f(x).")
    return suggestions


def build_conversion_failure_insight(
    *, latex: str, error_type: str, message: str, source_location: str | None = None
) -> dict[str, Any]:
    """Generate actionable failure guidance for conversion errors."""
    normalized = normalize_latex_for_sympy(latex)
    return {
        "severity": _failure_severity(latex, source_location),
        "reason": "conversion failure",
        "error_type": error_type,
        "error_message": message,
        "explanation": _failure_explanation(message),
        "suggested_fixes": _fix_suggestions(latex),
        "sympy_friendly_alternative": normalized,
        "before_after": {"before": latex, "after": normalized},
        "docs_link": "https://docs.sympy.org/latest/modules/parsing.html",
    }


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
                status="FAIL",
                reason="extraction failure",
                errors=extraction.errors,
                metadata={"artifact_path": str(artifact_path), "conversions": []},
            )

        conversions: list[dict[str, Any]] = []
        errors: list[str] = []
        failed = 0
        for equation in extraction.metadata.get("equations", []):
            eq_result = convert_equation(equation["lhs"], equation["rhs"])

            insight = None
            if eq_result.error:
                failed += 1
                insight = build_conversion_failure_insight(
                    latex=equation["raw"],
                    error_type=eq_result.error.error_type,
                    message=eq_result.error.message,
                    source_location=equation.get("source_location"),
                )
                first_fix = insight["suggested_fixes"][0] if insight["suggested_fixes"] else ""
                errors.append(
                    f"Equation conversion failed at {equation['source_location']}: "
                    f"{eq_result.error.message}. Suggested fix: {first_fix}"
                )

            conversions.append(
                {
                    "source_location": equation["source_location"],
                    "raw": equation["raw"],
                    "lhs_sympy": None if eq_result.error else str(eq_result.lhs_sympy),
                    "rhs_sympy": None if eq_result.error else str(eq_result.rhs_sympy),
                    "error": asdict(eq_result.error) if eq_result.error else None,
                    "failure_insight": insight,
                }
            )

        total = len(conversions)
        converted = total - failed
        score = 0.0 if total == 0 else round((converted / total) * 10.0, 2)

        return ValidationResult(
            name=self.name,
            passed=not errors,
            status="PASS" if not errors else "FAIL",
            errors=errors,
            metadata={
                "artifact_path": str(artifact_path),
                "conversion_count": len(conversions),
                "conversions": conversions,
                "convertibility": {
                    "total_equations": total,
                    "convertible_equations": converted,
                    "failed_equations": failed,
                    "score_out_of_10": score,
                },
            },
        )
