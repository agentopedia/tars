from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from tars.validators.base import BaseValidator
from tars.validators.result import ValidationResult

from .math_converter import MathConverter, convert_equation
from .math_extractor import MathExtractor
from .numeric_validator import NumericValidator
from .symbolic_validator import SymbolicValidator


logger = logging.getLogger(__name__)


class MathValidator(BaseValidator):
    """Coordinate extraction/conversion/symbolic/numeric validation for math equations."""

    name = "math_validator"
    artifact_type = "research-paper"

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
        return (
            "symbolic validation failed" in error_text
            or "sympy is not available" in error_text
        )

    def _validate_one_equation(self, equation: dict[str, Any]) -> dict[str, Any]:
        eq_result: dict[str, Any] = {
            "source_location": equation["source_location"],
            "raw": equation["raw"],
            "decision_path": [],
            "passed": False,
            "errors": [],
        }

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

        logger.info("math_validator decision path: symbolic_inconclusive_numeric_attempt", extra={"source": equation["source_location"]})
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
                errors.extend(
                    [f"{item['source_location']}: {err}" for err in item.get("errors", [])]
                )

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
