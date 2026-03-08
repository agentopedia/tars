from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from tars.validators.base import BaseValidator
from tars.validators.result import ValidationResult

from .math_converter import convert_equation, convert_latex_to_sympy
from .math_extractor import MathExtractor
from .numeric_validator import NumericValidator
from .symbolic_validator import SymbolicValidator

logger = logging.getLogger(__name__)


class MathValidator(BaseValidator):
    """Coordinate extraction/conversion/symbolic/numeric validation for math equations."""

    name = "math_validator"
    artifact_type = "research-paper"

    _DERIVATIVE_PATTERN = re.compile(r"\\frac\s*\{d\}\s*\{d\s*([A-Za-z])\}\s*(.+)$", re.DOTALL)
    _INTEGRAL_PATTERN = re.compile(r"\\int\s+(.+?)\s*(?:\\,\s*)?d\s*([A-Za-z])\s*$", re.DOTALL)

    def __init__(self) -> None:
        self.extractor = MathExtractor()
        self.symbolic_validator = SymbolicValidator()
        self.numeric_validator = NumericValidator()

    @staticmethod
    def _mark_skipped(eq_result: dict[str, Any], reason: str = "conversion failure") -> None:
        eq_result["status"] = "SKIPPED"
        eq_result["reason"] = reason
        eq_result["passed"] = False

    @staticmethod
    def _symbolic_inconclusive(symbolic_result: ValidationResult) -> bool:
        if symbolic_result.passed:
            return False
        if not symbolic_result.errors:
            return True
        error_text = " ".join(symbolic_result.errors).lower()
        return "symbolic validation failed" in error_text or "sympy is not available" in error_text

    def _validate_derivative_equation(self, equation: dict[str, Any], eq_result: dict[str, Any]) -> bool:
        lhs_latex = equation["lhs"].strip()
        match = self._DERIVATIVE_PATTERN.match(lhs_latex)
        if not match:
            return False

        eq_result["decision_path"].append("derivative_detected")
        variable_name, target_expr_latex = match.group(1), match.group(2).strip()
        rhs_latex = equation["rhs"].strip()

        target_expr = convert_latex_to_sympy(target_expr_latex)
        if hasattr(target_expr, "error_type"):
            eq_result["decision_path"].append("derivative_conversion_failed")
            self._mark_skipped(eq_result, "conversion failure")
            eq_result["errors"].append(f"Derivative conversion failed for target expression: {target_expr.message}")
            return True

        rhs_expr = convert_latex_to_sympy(rhs_latex)
        if hasattr(rhs_expr, "error_type"):
            eq_result["decision_path"].append("derivative_conversion_failed")
            self._mark_skipped(eq_result, "conversion failure")
            eq_result["errors"].append(f"Derivative conversion failed for rhs expression: {rhs_expr.message}")
            return True

        try:
            import sympy as sp  # type: ignore
        except Exception as exc:
            eq_result["decision_path"].append("derivative_sympy_unavailable")
            self._mark_skipped(eq_result, "sympy unavailable")
            eq_result["errors"].append(f"SymPy is not available: {exc}")
            return True

        derivative_expr = sp.diff(target_expr, sp.Symbol(variable_name))
        eq_result["decision_path"].append("derivative_diff_computed")
        symbolic = self.symbolic_validator.validate_equivalence(derivative_expr, rhs_expr)
        eq_result["symbolic"] = symbolic.to_dict()

        if symbolic.passed:
            eq_result["decision_path"].append("derivative_pass")
            eq_result["status"] = "PASS"
            eq_result["passed"] = True
            return True

        eq_result["decision_path"].append("derivative_fail")
        eq_result["status"] = "FAIL"
        eq_result["errors"].extend(symbolic.errors)
        return True

    def _validate_integral_equation(self, equation: dict[str, Any], eq_result: dict[str, Any]) -> bool:
        lhs_latex = equation["lhs"].strip()
        match = self._INTEGRAL_PATTERN.match(lhs_latex)
        if not match:
            return False

        eq_result["decision_path"].append("integral_detected")
        integrand_latex, variable_name = match.group(1).strip(), match.group(2)
        rhs_latex = equation["rhs"].strip()

        integrand_expr = convert_latex_to_sympy(integrand_latex)
        if hasattr(integrand_expr, "error_type"):
            eq_result["decision_path"].append("integral_conversion_failed")
            self._mark_skipped(eq_result, "conversion failure")
            eq_result["errors"].append(f"Integral conversion failed for integrand: {integrand_expr.message}")
            return True

        rhs_expr = convert_latex_to_sympy(rhs_latex)
        if hasattr(rhs_expr, "error_type"):
            eq_result["decision_path"].append("integral_conversion_failed")
            self._mark_skipped(eq_result, "conversion failure")
            eq_result["errors"].append(f"Integral conversion failed for rhs expression: {rhs_expr.message}")
            return True

        try:
            import sympy as sp  # type: ignore
        except Exception as exc:
            eq_result["decision_path"].append("integral_sympy_unavailable")
            self._mark_skipped(eq_result, "sympy unavailable")
            eq_result["errors"].append(f"SymPy is not available: {exc}")
            return True

        integrated_expr = sp.integrate(integrand_expr, sp.Symbol(variable_name))
        eq_result["decision_path"].append("integral_computed")
        symbolic = self.symbolic_validator.validate_equivalence(integrated_expr, rhs_expr)
        eq_result["symbolic"] = symbolic.to_dict()

        if symbolic.passed:
            eq_result["decision_path"].append("integral_pass")
            eq_result["status"] = "PASS"
            eq_result["passed"] = True
            return True

        eq_result["decision_path"].append("integral_fail")
        eq_result["status"] = "FAIL"
        eq_result["errors"].extend(symbolic.errors)
        return True

    def _validate_one_equation(self, equation: dict[str, Any]) -> dict[str, Any]:
        eq_result: dict[str, Any] = {
            "source_location": equation["source_location"],
            "raw": equation["raw"],
            "decision_path": [],
            "passed": False,
            "status": "FAIL",
            "reason": None,
            "errors": [],
        }

        try:
            if self._validate_derivative_equation(equation, eq_result):
                return eq_result

            if self._validate_integral_equation(equation, eq_result):
                return eq_result

            conversion = convert_equation(equation["lhs"], equation["rhs"])
            if conversion.error is not None:
                eq_result["decision_path"].append("conversion_failed")
                self._mark_skipped(eq_result, "conversion failure")
                eq_result["errors"].append(f"Conversion failed: {conversion.error.message}")
                return eq_result

            lhs_sympy = conversion.lhs_sympy
            rhs_sympy = conversion.rhs_sympy

            eq_result["decision_path"].append("symbolic_attempt")
            symbolic = self.symbolic_validator.validate_equivalence(lhs_sympy, rhs_sympy)
            eq_result["symbolic"] = symbolic.to_dict()

            if symbolic.passed:
                eq_result["decision_path"].append("symbolic_pass")
                eq_result["status"] = "PASS"
                eq_result["passed"] = True
                return eq_result

            if not self._symbolic_inconclusive(symbolic):
                eq_result["decision_path"].append("symbolic_fail")
                eq_result["status"] = "FAIL"
                eq_result["errors"].extend(symbolic.errors)
                return eq_result

            eq_result["decision_path"].append("symbolic_inconclusive")
            eq_result["decision_path"].append("numeric_attempt")
            numeric = self.numeric_validator.validate_equivalence(lhs_sympy, rhs_sympy)
            eq_result["numeric"] = numeric.to_dict()

            if numeric.passed:
                eq_result["decision_path"].append("numeric_pass")
                eq_result["status"] = "PASS"
                eq_result["passed"] = True
                return eq_result

            eq_result["decision_path"].append("numeric_fail")
            eq_result["status"] = "FAIL"
            eq_result["errors"].extend(numeric.errors)
            return eq_result
        except Exception as exc:
            logger.exception("math_validator decision path: equation_processing_exception")
            eq_result["decision_path"].append("equation_processing_exception")
            self._mark_skipped(eq_result, "conversion failure")
            eq_result["errors"].append(f"Equation processing failed: {exc}")
            return eq_result

    def validate(self, artifact_path: Path) -> ValidationResult:
        extraction = self.extractor.validate(artifact_path)
        if not extraction.passed:
            return ValidationResult(
                name=self.name,
                passed=False,
                status="FAIL",
                reason="extraction failure",
                errors=extraction.errors,
                metadata={"artifact_path": str(artifact_path), "equations": []},
            )

        equations = extraction.metadata.get("equations", [])
        details = [self._validate_one_equation(eq) for eq in equations]

        errors: list[str] = []
        skipped_count = 0
        for item in details:
            if item.get("status") == "SKIPPED":
                skipped_count += 1
                continue
            if not item["passed"]:
                errors.extend([f"{item['source_location']}: {err}" for err in item.get("errors", [])])

        status = "FAIL" if errors else ("SKIPPED" if skipped_count else "PASS")
        reason = "conversion failure" if status == "SKIPPED" else None

        return ValidationResult(
            name=self.name,
            passed=not errors,
            status=status,
            reason=reason,
            errors=errors,
            metadata={
                "artifact_path": str(artifact_path),
                "equation_count": len(equations),
                "skipped_count": skipped_count,
                "results": details,
            },
        )
