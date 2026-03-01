from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tars.validators.research.math.math_extractor import MathExtractor


class MathExtractorTests(unittest.TestCase):
    def test_extracts_supported_math_environments(self):
        tex_path = Path("examples/latex/sample_math.tex")
        extractor = MathExtractor()

        result = extractor.validate(tex_path)

        self.assertTrue(result.passed)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.metadata["expression_count"], 5)

        exprs = result.metadata["expressions"]
        envs = [e["environment_type"] for e in exprs]

        self.assertEqual(envs.count("inline"), 2)
        self.assertIn("display_brackets", envs)
        self.assertIn("equation", envs)
        self.assertIn("align", envs)

        # Ensure multiline inline math is captured
        inline_raw = "\n".join([e["raw_latex"] for e in exprs if e["environment_type"] == "inline"])
        self.assertIn("$\\alpha +\n\\beta$", inline_raw)

        # Ensure line numbers are reported
        self.assertTrue(all(isinstance(e["line_number"], int) and e["line_number"] > 0 for e in exprs))

    def test_non_tex_file_fails_validation(self):
        extractor = MathExtractor()
        result = extractor.validate(Path("README.md"))

        self.assertFalse(result.passed)
        self.assertIn("Expected a .tex file", result.errors)


if __name__ == "__main__":
    unittest.main()
