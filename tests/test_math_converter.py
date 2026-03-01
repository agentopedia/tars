from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tars.validators.research.math.math_converter import (
    ConversionError,
    convert_latex_to_sympy,
    convert_latex_to_sympy_result,
)


HAS_LATEX2SYMPY2 = importlib.util.find_spec("latex2sympy2") is not None


@unittest.skipUnless(HAS_LATEX2SYMPY2, "latex2sympy2 not installed")
class MathConverterConversionTests(unittest.TestCase):
    def test_fraction_conversion(self):
        expr = convert_latex_to_sympy(r"\\frac{1}{2}")
        self.assertFalse(isinstance(expr, ConversionError))

    def test_power_conversion(self):
        expr = convert_latex_to_sympy(r"x^2")
        self.assertFalse(isinstance(expr, ConversionError))

    def test_trigonometric_conversion(self):
        expr = convert_latex_to_sympy(r"\\sin(x)")
        self.assertFalse(isinstance(expr, ConversionError))

    def test_integral_conversion(self):
        expr = convert_latex_to_sympy(r"\\int_0^1 x^2 \\; dx")
        self.assertFalse(isinstance(expr, ConversionError))

    def test_derivative_conversion(self):
        expr = convert_latex_to_sympy(r"\\frac{d}{dx}x^2")
        self.assertFalse(isinstance(expr, ConversionError))


class MathConverterFailureTests(unittest.TestCase):
    def test_conversion_failure_returns_structured_error(self):
        result = convert_latex_to_sympy_result(r"\\thisisnotvalid{")
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error)
        self.assertIsInstance(result.error, ConversionError)
        self.assertEqual(result.error.latex, r"\\thisisnotvalid{")


if __name__ == "__main__":
    unittest.main()
