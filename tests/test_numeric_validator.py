from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tars.validators.research.math.numeric_validator import NumericValidator


HAS_SYMPY = importlib.util.find_spec("sympy") is not None


@unittest.skipUnless(HAS_SYMPY, "sympy not installed")
class NumericValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = NumericValidator()
        import sympy as sp

        self.sp = sp

    def test_polynomial_equivalence_passes(self):
        x = self.sp.Symbol("x")
        lhs = (x + 1) ** 2
        rhs = x**2 + 2 * x + 1
        result = self.validator.validate_equivalence(lhs, rhs, trials=8, seed=42)
        self.assertTrue(result.passed)

    def test_incorrect_algebra_fails(self):
        x = self.sp.Symbol("x")
        lhs = (x + 1) ** 2
        rhs = x**2 + 1
        result = self.validator.validate_equivalence(lhs, rhs, trials=8, seed=42)
        self.assertFalse(result.passed)
        self.assertIn("Numeric mismatch", result.errors[0])

    def test_trigonometric_identity_passes(self):
        x = self.sp.Symbol("x")
        lhs = self.sp.sin(x) ** 2 + self.sp.cos(x) ** 2
        rhs = self.sp.Integer(1)
        result = self.validator.validate_equivalence(lhs, rhs, trials=8, seed=7)
        self.assertTrue(result.passed)

    def test_exponential_identity_passes(self):
        x = self.sp.Symbol("x")
        lhs = self.sp.exp(x)
        rhs = 1 / self.sp.exp(-x)
        result = self.validator.validate_equivalence(lhs, rhs, trials=8, seed=7)
        self.assertTrue(result.passed)

    def test_incorrect_log_identity_fails(self):
        a, b = self.sp.symbols("a b", positive=True)
        lhs = self.sp.log(a + b)
        rhs = self.sp.log(a) + self.sp.log(b)
        result = self.validator.validate_equivalence(lhs, rhs, trials=10, seed=12)
        self.assertFalse(result.passed)

    def test_resamples_around_division_by_zero(self):
        x = self.sp.Symbol("x")
        lhs = 1 / (x - 1)
        rhs = 1 / (x - 1)
        result = self.validator.validate_equivalence(lhs, rhs, trials=8, seed=1)
        self.assertTrue(result.passed)


class NumericValidatorPathTests(unittest.TestCase):
    def test_validate_path_returns_structured_result(self):
        v = NumericValidator()
        result = v.validate(Path("paper.tex"))
        self.assertFalse(result.passed)
        self.assertIn("Path-based numeric validation", result.errors[0])


if __name__ == "__main__":
    unittest.main()
