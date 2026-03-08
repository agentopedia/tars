from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tars.validators.research.math.symbolic_validator import SymbolicValidator


HAS_SYMPY = importlib.util.find_spec("sympy") is not None


@unittest.skipUnless(HAS_SYMPY, "sympy not installed")
class SymbolicValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = SymbolicValidator()
        import sympy as sp

        self.sp = sp

    def test_correct_algebra_passes(self):
        x = self.sp.Symbol("x")
        lhs = (x + 1) ** 2
        rhs = x**2 + 2 * x + 1
        result = self.validator.validate_equivalence(lhs, rhs)
        self.assertTrue(result.passed)

    def test_polynomial_equivalence_passes(self):
        x = self.sp.Symbol("x")
        lhs = x**2 - 1
        rhs = (x - 1) * (x + 1)
        result = self.validator.validate_equivalence(lhs, rhs)
        self.assertTrue(result.passed)

    def test_incorrect_algebra_fails(self):
        x = self.sp.Symbol("x")
        lhs = (x + 1) ** 2
        rhs = x**2 + 1
        result = self.validator.validate_equivalence(lhs, rhs)
        self.assertFalse(result.passed)

    def test_incorrect_identity_fails(self):
        x = self.sp.Symbol("x")
        lhs = self.sp.sin(x) ** 2 + self.sp.cos(x) ** 2
        rhs = self.sp.Integer(0)
        result = self.validator.validate_equivalence(lhs, rhs)
        self.assertFalse(result.passed)

    def test_trigonometric_identity_passes(self):
        x = self.sp.Symbol("x")
        lhs = self.sp.sin(x) ** 2 + self.sp.cos(x) ** 2
        rhs = self.sp.Integer(1)
        result = self.validator.validate_equivalence(lhs, rhs)
        self.assertTrue(result.passed)

    def test_exponential_identity_passes(self):
        x = self.sp.Symbol("x")
        lhs = self.sp.exp(x)
        rhs = 1 / self.sp.exp(-x)
        result = self.validator.validate_equivalence(lhs, rhs)
        self.assertTrue(result.passed)

    def test_incorrect_log_identity_fails(self):
        a, b = self.sp.symbols("a b", positive=True)
        lhs = self.sp.log(a + b)
        rhs = self.sp.log(a) + self.sp.log(b)
        result = self.validator.validate_equivalence(lhs, rhs)
        self.assertFalse(result.passed)

    def test_matrix_expressions(self):
        a = self.sp.Matrix([[1, 2], [3, 4]])
        b = self.sp.Matrix([[2, 1], [0, 5]])
        lhs = a + b
        rhs = self.sp.Matrix([[3, 3], [3, 9]])
        result = self.validator.validate_equivalence(lhs, rhs)
        self.assertTrue(result.passed)


class SymbolicValidatorNoSympyTests(unittest.TestCase):
    def test_validate_path_returns_structured_result(self):
        v = SymbolicValidator()
        result = v.validate(Path("paper.tex"))
        self.assertFalse(result.passed)
        self.assertIn("Path-based symbolic validation", result.errors[0])


if __name__ == "__main__":
    unittest.main()
