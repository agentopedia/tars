from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tars.validators.research.math.dimensional_validator import DimensionalValidator


HAS_PINT = importlib.util.find_spec("pint") is not None


@unittest.skipUnless(HAS_PINT, "pint not installed")
class DimensionalValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = DimensionalValidator()

    def test_compatible_units_pass(self):
        result = self.validator.validate_units("meter / second", "kilometer / hour")
        self.assertTrue(result.passed)
        self.assertEqual("PASS", result.status)

    def test_incompatible_units_fail(self):
        result = self.validator.validate_units("meter", "second")
        self.assertFalse(result.passed)
        self.assertEqual("FAIL", result.status)
        self.assertEqual("unit mismatch", result.reason)

    def test_invalid_unit_math_detected(self):
        result = self.validator.validate_units("meter + second", "meter")
        self.assertFalse(result.passed)
        self.assertIn(result.reason, {"conversion failure", "invalid unit math"})


class DimensionalValidatorPathTests(unittest.TestCase):
    def test_validate_path_returns_structured_result(self):
        result = DimensionalValidator().validate(Path("paper.tex"))
        self.assertFalse(result.passed)
        self.assertEqual("SKIPPED", result.status)


if __name__ == "__main__":
    unittest.main()
