from __future__ import annotations

import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tars.cli import main
from tars.summarizers import MathValidationSummarizer
from tars.validators.result import ValidationResult


class TarsCliTests(unittest.TestCase):
    def test_validate_math_prints_summary_and_findings(self):
        fake_result = ValidationResult(
            name="math_validator",
            passed=True,
            status="PASS",
            reason=None,
            errors=[],
            metadata={
                "metrics": {
                    "total_equations": 12,
                    "validated_equations": 10,
                    "failed_equations": 1,
                    "skipped_equations": 2,
                }
            },
        )

        with (
            patch("tars.cli.MathValidator.validate", return_value=fake_result),
            patch.object(MathValidationSummarizer, "summarize", return_value="Readable findings."),
        ):
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                code = main(["validate-math", "paper.tex"])

        output = buffer.getvalue()
        self.assertEqual(0, code)
        self.assertIn("Math validation: status=PASS", output)
        self.assertIn("total_equations=12", output)
        self.assertIn("validated_equations=10", output)
        self.assertIn("failed_equations=1", output)
        self.assertIn("skipped_equations=2", output)
        self.assertIn("Findings: Readable findings.", output)


class MathValidationSummarizerTests(unittest.TestCase):
    def test_fallback_without_api_key(self):
        result = ValidationResult(
            name="math_validator",
            passed=False,
            status="FAIL",
            reason=None,
            errors=["eq 1 failed"],
            metadata={
                "metrics": {
                    "total_equations": 4,
                    "validated_equations": 4,
                    "failed_equations": 1,
                    "skipped_equations": 0,
                }
            },
        )

        with patch.dict("os.environ", {}, clear=True):
            text = MathValidationSummarizer().summarize(result)

        self.assertIn("Deterministic validation found 1 failed equation", text)


if __name__ == "__main__":
    unittest.main()
