from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from tars.validators.base import BaseValidator
from tars.validators.result import ValidationResult

from .math_converter import MathConverter, convert_equation, convert_latex_to_sympy
from .math_extractor import MathExtractor
from .numeric_validator import NumericValidator
from .symbolic_validator import SymbolicValidator


logger = logging.getLogger(__name__)


class MathValidator(BaseValidator):
    """Coordinate extraction/conversion/symbolic/numeric validation for math equations."""

    name = "math_validator"
    artifact_type = "research-paper"

    _DERIVATIVE_PATTERN = re.compile(r"\\frac\s*\{d\}\s*\{d\s*([A-Za-z])\}\s*(.+)$", re.DOTALL)

    def __init__(self) -> None:
        self.extractor = MathExtractor()
        self.converter = MathConverter()
        self.symbolic_validator = SymbolicValidator()
        self.numeric_validator = NumericValidator()

    @staticmethod
    def _symbolic_inconclusive(symbolic_result: ValidationResult) -> bool:
        """Return True when symbolic result should defer to numeric validation."""
        if symbolic_result.passed:
            return False
        if not symbolic_result.errors:
            return True

        error_text = " ".join(symbolic_result.errors).lower()
        return "symbolic validation failed" in error_text or "sympy is not available" in error_text

    def _validate_derivative_equation(self, equation: dict[str, Any], eq_result: dict[str, Any]) -> bool:
        """Detect and validate equations of form ``\frac{d}{dx} f(x) = g(x)``."""
        lhs_latex = equation["lhs"].strip()
        match = self._DERIVATIVE_PATTERN.match(lhs_latex)
        if not match:
            return False

        eq_result["decision_path"].append("derivative_detected")
        logger.info("math_validator decision path: derivative_detected", extra={"source": equation["source_location"]})

        variable_name, target_expr_latex = match.group(1), match.group(2).strip()
        rhs_latex = equation["rhs"].strip()

        target_expr = convert_latex_to_sympy(target_expr_latex)
        if hasattr(target_expr, "error_type"):
            eq_result["decision_path"].append("derivative_conversion_failed")
            eq_result["errors"].append(f"Derivative conversion failed for target expression: {target_expr.message}")
            return True

        rhs_expr = convert_latex_to_sympy(rhs_latex)
        if hasattr(rhs_expr, "error_type"):
            eq_result["decision_path"].append("derivative_conversion_failed")
            eq_result["errors"].append(f"Derivative conversion failed for rhs expression: {rhs_expr.message}")
            return True

        try:
            import sympy as sp  # type: ignore
        except Exception as exc:
            eq_result["decision_path"].append("derivative_sympy_unavailable")
            eq_result["errors"].append(f"SymPy is not available: {exc}")
            return True

        derivative_expr = sp.diff(target_expr, sp.Symbol(variable_name))
        eq_result["decision_path"].append("derivative_diff_computed")
        logger.info("math_validator decision path: derivative_diff_computed", extra={"source": equation["source_location"]})

        symbolic = self.symbolic_validator.validate_equivalence(derivative_expr, rhs_expr)
        eq_result["symbolic"] = symbolic.to_dict()

        if symbolic.passed:
            eq_result["decision_path"].append("derivative_pass")
            logger.info("math_validator decision path: derivative_pass", extra={"source": equation["source_location"]})
            eq_result["passed"] = True
            return True

        eq_result["decision_path"].append("derivative_fail")
        logger.info("math_validator decision path: derivative_fail", extra={"source": equation["source_location"]})
        eq_result["errors"].extend(symbolic.errors)
        return True

    def _validate_one_equation(self, equation: dict[str, Any]) -> dict[str, Any]:
        eq_result: dict[str, Any] = {
            "source_location": equation["source_location"],
            "raw": equation["raw"],
            "decision_path": [],
            "passed": False,
            "errors": [],
        }

        if self._validate_derivative_equation(equation, eq_result):
            return eq_result

        conversion = convert_equation(equation["lhs"], equation["rhs"])
        if conversion.error is not None:
            msg = f"Conversion failed: {conversion.error.message}"
            logger.info("math_validator decision path: conversion_failed", extra={"source": equation["source_location"]})
            eq_result["decision_path"].append("conversion_failed")
            eq_result["errors"].append(msg)
            return eq_result

        lhs_sympy = conversion.lhs_sympy
        rhs_sympy = conversion.rhs_sympy

        logger.info("math_validator decision path: symbolic_attempt", extra={"source": equation["source_location"]})
        eq_result["decision_path"].append("symbolic_attempt")
        symbolic = self.symbolic_validator.validate_equivalence(lhs_sympy, rhs_sympy)
        eq_result["symbolic"] = symbolic.to_dict()

        if symbolic.passed:
            logger.info("math_validator decision path: symbolic_pass", extra={"source": equation["source_location"]})
            eq_result["decision_path"].append("symbolic_pass")
            eq_result["passed"] = True
            return eq_result

        if not self._symbolic_inconclusive(symbolic):
            logger.info("math_validator decision path: symbolic_fail", extra={"source": equation["source_location"]})
            eq_result["decision_path"].append("symbolic_fail")
            eq_result["errors"].extend(symbolic.errors)
            return eq_result

        logger.info(
            "math_validator decision path: symbolic_inconclusive_numeric_attempt",
            extra={"source": equation["source_location"]},
        )
        eq_result["decision_path"].append("symbolic_inconclusive")
        eq_result["decision_path"].append("numeric_attempt")
        numeric = self.numeric_validator.validate_equivalence(lhs_sympy, rhs_sympy)
        eq_result["numeric"] = numeric.to_dict()

        if numeric.passed:
            logger.info("math_validator decision path: numeric_pass", extra={"source": equation["source_location"]})
            eq_result["decision_path"].append("numeric_pass")
            eq_result["passed"] = True
            return eq_result

        logger.info("math_validator decision path: numeric_fail", extra={"source": equation["source_location"]})
        eq_result["decision_path"].append("numeric_fail")
        eq_result["errors"].extend(numeric.errors)
        return eq_result

    def validate(self, artifact_path: Path) -> ValidationResult:
        """Run math validation pipeline with symbolic-first and numeric fallback."""
        extraction = self.extractor.validate(artifact_path)
        if not extraction.passed:
            return ValidationResult(
                name=self.name,
                passed=False,
                errors=extraction.errors,
                metadata={"artifact_path": str(artifact_path), "equations": []},
            )

        equations = extraction.metadata.get("equations", [])
        details = [self._validate_one_equation(eq) for eq in equations]
        errors: list[str] = []
        for item in details:
            if not item["passed"]:
                errors.extend([f"{item['source_location']}: {err}" for err in item.get("errors", [])])

        logger.info(
            "math_validator completed",
            extra={
                "artifact_path": str(artifact_path),
                "equation_count": len(equations),
                "passed_count": sum(1 for d in details if d["passed"]),
            },
        )

        return ValidationResult(
            name=self.name,
            passed=not errors,
            errors=errors,
            metadata={
                "artifact_path": str(artifact_path),
                "equation_count": len(equations),
                "results": details,
            },
        )
