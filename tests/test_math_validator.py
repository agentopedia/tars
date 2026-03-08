from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tars.validators.research.math.math_validator import MathValidator
from tars.validators.result import ValidationResult


class MathValidatorPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = MathValidator()

    @staticmethod
    def _fake_extraction_result() -> ValidationResult:
        return ValidationResult(
            name="math_extractor",
            passed=True,
            errors=[],
            metadata={
                "equations": [
                    {
                        "lhs": "x+1",
                        "rhs": "1+x",
                        "raw": "x+1=1+x",
                        "source_location": "line:1:inline",
                    }
                ]
            },
        )

    @staticmethod
    def _fake_conversion_result():
        class _Obj:
            error = None
            lhs_sympy = "lhs_expr"
            rhs_sympy = "rhs_expr"

        return _Obj()

    def test_symbolic_pass_short_circuits_numeric(self):
        symbolic_pass = ValidationResult(name="symbolic_validator", passed=True, errors=[], metadata={})

        with patch.object(self.validator.extractor, "validate", return_value=self._fake_extraction_result()), patch(
            "tars.validators.research.math.math_validator.convert_equation",
            return_value=self._fake_conversion_result(),
        ), patch.object(
            self.validator.symbolic_validator,
            "validate_equivalence",
            return_value=symbolic_pass,
        ), patch.object(
            self.validator.numeric_validator,
            "validate_equivalence",
        ) as numeric_call:
            result = self.validator.validate(Path("paper.tex"))

        self.assertTrue(result.passed)
        self.assertEqual([], result.errors)
        self.assertFalse(numeric_call.called)
        decision_path = result.metadata["results"][0]["decision_path"]
        self.assertEqual(["symbolic_attempt", "symbolic_pass"], decision_path)

    def test_symbolic_inconclusive_falls_back_to_numeric(self):
        symbolic_inconclusive = ValidationResult(
            name="symbolic_validator",
            passed=False,
            errors=["Symbolic validation failed: indeterminate"],
            metadata={},
        )
        numeric_pass = ValidationResult(name="numeric_validator", passed=True, errors=[], metadata={})

        with patch.object(self.validator.extractor, "validate", return_value=self._fake_extraction_result()), patch(
            "tars.validators.research.math.math_validator.convert_equation",
            return_value=self._fake_conversion_result(),
        ), patch.object(
            self.validator.symbolic_validator,
            "validate_equivalence",
            return_value=symbolic_inconclusive,
        ), patch.object(
            self.validator.numeric_validator,
            "validate_equivalence",
            return_value=numeric_pass,
        ) as numeric_call:
            result = self.validator.validate(Path("paper.tex"))

        self.assertTrue(result.passed)
        self.assertTrue(numeric_call.called)
        decision_path = result.metadata["results"][0]["decision_path"]
        self.assertEqual(
            ["symbolic_attempt", "symbolic_inconclusive", "numeric_attempt", "numeric_pass"],
            decision_path,
        )

    def test_symbolic_definitive_fail_does_not_run_numeric(self):
        symbolic_fail = ValidationResult(
            name="symbolic_validator",
            passed=False,
            errors=["Expressions are not mathematically equivalent"],
            metadata={},
        )

        with patch.object(self.validator.extractor, "validate", return_value=self._fake_extraction_result()), patch(
            "tars.validators.research.math.math_validator.convert_equation",
            return_value=self._fake_conversion_result(),
        ), patch.object(
            self.validator.symbolic_validator,
            "validate_equivalence",
            return_value=symbolic_fail,
        ), patch.object(
            self.validator.numeric_validator,
            "validate_equivalence",
        ) as numeric_call:
            result = self.validator.validate(Path("paper.tex"))

        self.assertFalse(result.passed)
        self.assertFalse(numeric_call.called)
        decision_path = result.metadata["results"][0]["decision_path"]
        self.assertEqual(["symbolic_attempt", "symbolic_fail"], decision_path)

    def test_numeric_fail_propagates(self):
        symbolic_inconclusive = ValidationResult(
            name="symbolic_validator",
            passed=False,
            errors=["Symbolic validation failed: timeout"],
            metadata={},
        )
        numeric_fail = ValidationResult(
            name="numeric_validator",
            passed=False,
            errors=["Numeric mismatch detected"],
            metadata={},
        )

        with patch.object(self.validator.extractor, "validate", return_value=self._fake_extraction_result()), patch(
            "tars.validators.research.math.math_validator.convert_equation",
            return_value=self._fake_conversion_result(),
        ), patch.object(
            self.validator.symbolic_validator,
            "validate_equivalence",
            return_value=symbolic_inconclusive,
        ), patch.object(
            self.validator.numeric_validator,
            "validate_equivalence",
            return_value=numeric_fail,
        ):
            result = self.validator.validate(Path("paper.tex"))

        self.assertFalse(result.passed)
        self.assertIn("Numeric mismatch detected", " ".join(result.errors))
        decision_path = result.metadata["results"][0]["decision_path"]
        self.assertEqual(
            ["symbolic_attempt", "symbolic_inconclusive", "numeric_attempt", "numeric_fail"],
            decision_path,
        )


if __name__ == "__main__":
    unittest.main()
