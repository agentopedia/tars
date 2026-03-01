from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tars.validators import ValidationIssue, ValidationResult


class ValidatorNamespaceTests(unittest.TestCase):
    def test_validator_namespace_types(self):
        issue = ValidationIssue(code="LATEX_001", message="Missing \\begin{document}")
        result = ValidationResult(
            validator_name="latex",
            passed=False,
            issues=[issue],
            metadata={"phase": "mvp"},
        )

        self.assertEqual(result.validator_name, "latex")
        self.assertFalse(result.passed)
        self.assertEqual(result.issues[0].code, "LATEX_001")


if __name__ == "__main__":
    unittest.main()
