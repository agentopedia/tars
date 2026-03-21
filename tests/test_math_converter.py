from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tars.validators.research.math.math_converter import (
    ConversionError,
    EquationConversionResult,
    MathConverter,
    build_conversion_failure_insight,
    convert_equation,
    convert_latex_to_sympy,
    convert_latex_to_sympy_result,
    normalize_latex_for_sympy,
)
from tars.validators.result import ValidationResult


HAS_LATEX2SYMPY2 = importlib.util.find_spec("latex2sympy2") is not None


@unittest.skipUnless(HAS_LATEX2SYMPY2, "latex2sympy2 not installed")
class MathConverterConversionTests(unittest.TestCase):
    def test_fraction_conversion(self):
        expr = convert_latex_to_sympy(r"\frac{1}{2}")
        self.assertFalse(isinstance(expr, ConversionError))

    def test_power_conversion(self):
        expr = convert_latex_to_sympy(r"x^2")
        self.assertFalse(isinstance(expr, ConversionError))

    def test_trigonometric_conversion(self):
        expr = convert_latex_to_sympy(r"\sin(x)")
        self.assertFalse(isinstance(expr, ConversionError))

    def test_integral_conversion(self):
        expr = convert_latex_to_sympy(r"\int x dx")
        self.assertFalse(isinstance(expr, ConversionError))

    def test_derivative_conversion(self):
        expr = convert_latex_to_sympy(r"\frac{\partial u}{\partial x}")
        self.assertFalse(isinstance(expr, ConversionError))

    def test_convert_equation_success(self):
        result = convert_equation(r"x^2", r"y+1")
        self.assertIsNone(result.error)
        self.assertIsNotNone(result.lhs_sympy)
        self.assertIsNotNone(result.rhs_sympy)


class MathConverterFailureTests(unittest.TestCase):
    def test_conversion_failure_returns_structured_error(self):
        result = convert_latex_to_sympy_result(r"\\thisisnotvalid{")
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error)
        self.assertIsInstance(result.error, ConversionError)
        self.assertEqual(result.error.latex, r"\\thisisnotvalid{")

    def test_convert_equation_failure_returns_structured_error(self):
        result = convert_equation(r"\\thisisnotvalid{", r"x")
        self.assertIsNotNone(result.error)
        self.assertIsInstance(result.error, ConversionError)
        self.assertIsNone(result.lhs_sympy)
        self.assertIsNone(result.rhs_sympy)

    def test_failure_insight_contains_actionable_guidance(self):
        insight = build_conversion_failure_insight(
            latex=r"\\text{CFL} = x",
            error_type="ParseError",
            message="no viable alternative",
            source_location="line:10:equation",
        )
        self.assertEqual("CRITICAL", insight["severity"])
        self.assertTrue(insight["suggested_fixes"])
        self.assertIn("sympy_friendly_alternative", insight)
        self.assertIn("docs.sympy.org", insight["docs_link"])

    def test_validate_includes_convertibility_and_failure_insights(self):
        converter = MathConverter()
        extraction = ValidationResult(
            name="math_extractor",
            passed=True,
            errors=[],
            metadata={
                "equations": [
                    {"lhs": "x+1", "rhs": "1+x", "raw": "x+1=1+x", "source_location": "line:1:inline"},
                    {
                        "lhs": r"\\text{bad}",
                        "rhs": "x",
                        "raw": r"\\text{bad}=x",
                        "source_location": "line:2:equation",
                    },
                ]
            },
        )

        with patch.object(converter.extractor, "validate", return_value=extraction), patch(
            "tars.validators.research.math.math_converter.convert_equation",
            side_effect=[
                EquationConversionResult(lhs_sympy="a", rhs_sympy="b", error=None),
                EquationConversionResult(
                    error=ConversionError(latex=r"\\text{bad}=x", error_type="ParseError", message="bad token")
                ),
            ],
        ):
            result = converter.validate(Path("paper.tex"))

        convertibility = result.metadata["convertibility"]
        self.assertEqual(2, convertibility["total_equations"])
        self.assertEqual(1, convertibility["convertible_equations"])
        self.assertEqual(1, convertibility["failed_equations"])
        self.assertEqual(5.0, convertibility["score_out_of_10"])
        self.assertIsNotNone(result.metadata["conversions"][1]["failure_insight"])


class MathConverterNormalizationTests(unittest.TestCase):
    def test_strip_metadata_tags(self):
        latex = r"x + y \\label{eq:1} \\nonumber \\cite{abc}"
        out = normalize_latex_for_sympy(latex)
        self.assertNotIn(r"\\label", out)
        self.assertNotIn(r"\\nonumber", out)
        self.assertNotIn(r"\\cite", out)

    def test_simplify_mbox(self):
        out = normalize_latex_for_sympy(r"\\mbox{CFL} + 1")
        self.assertIn("CFL", out)
        self.assertNotIn(r"\\mbox", out)

    def test_standardize_differentials(self):
        out = normalize_latex_for_sympy(r"\\int_0^1 f(x) \\mathrm{d} x")
        self.assertIn("dx", out)
        self.assertNotIn(r"\\mathrm{d}", out)

    def test_prime_notation_rewrite(self):
        out = normalize_latex_for_sympy(r"f' + g''")
        self.assertIn("f_prime", out)
        self.assertIn("g_prime2", out)


if __name__ == "__main__":
    unittest.main()
