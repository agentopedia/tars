from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tars.validators import ValidationResult


class ValidatorNamespaceTests(unittest.TestCase):
    def test_validation_result_json_serializable(self):
        result = ValidationResult(
            name="latex",
            passed=False,
            errors=["Missing \\begin{document}", "Undefined citation: smith2024"],
            metadata={"phase": "mvp", "artifact": "paper.tex"},
        )

        payload = result.to_dict()
        encoded = json.dumps(payload)

        self.assertIn('"name": "latex"', encoded)
        self.assertIn('"passed": false', encoded)
        self.assertEqual(payload["errors"][0], "Missing \\begin{document}")


if __name__ == "__main__":
    unittest.main()
