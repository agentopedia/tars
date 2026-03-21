from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tars.validators.engine import ValidationEngine
from tars.validators.research.math.math_validator import MathValidator
from tars.validators.result import ValidationResult


class MathValidatorEngineIntegrationTests(unittest.TestCase):
    def test_engine_runs_math_validator_and_returns_aggregated_result(self):
        engine = ValidationEngine()
        validator = MathValidator()
        engine.register_validator(validator)

        extraction = ValidationResult(
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

        class _Conversion:
            error = None
            lhs_sympy = "lhs_expr"
            rhs_sympy = "rhs_expr"

        symbolic_inconclusive = ValidationResult(
            name="symbolic_validator",
            passed=False,
            errors=["Symbolic validation failed: indeterminate"],
            metadata={},
        )
        numeric_pass = ValidationResult(name="numeric_validator", passed=True, errors=[], metadata={})

        with patch.object(validator.extractor, "validate", return_value=extraction), patch(
            "tars.validators.research.math.math_validator.convert_equation",
            return_value=_Conversion(),
        ), patch.object(
            validator.symbolic_validator,
            "validate_equivalence",
            return_value=symbolic_inconclusive,
        ), patch.object(
            validator.numeric_validator,
            "validate_equivalence",
            return_value=numeric_pass,
        ):
            results = engine.run(Path("paper.tex"), validator_names=["math_validator"])

        self.assertEqual(1, len(results))
        result = results[0]
        self.assertEqual("math_validator", result.name)
        self.assertTrue(result.passed)
        self.assertEqual(
            {
                "total_equations": 1,
                "validated_equations": 1,
                "failed_equations": 0,
                "skipped_equations": 0,
            },
            result.metadata["metrics"],
        )


if __name__ == "__main__":
    unittest.main()
