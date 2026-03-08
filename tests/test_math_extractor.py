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

        inline_raw = "\n".join([e["raw_latex"] for e in exprs if e["environment_type"] == "inline"])
        self.assertIn("$\\alpha +\n\\beta$", inline_raw)
        self.assertTrue(all(isinstance(e["line_number"], int) and e["line_number"] > 0 for e in exprs))

    def test_normalizes_equations_with_lhs_rhs(self):
        extractor = MathExtractor()
        result = extractor.validate(Path("examples/latex/sample_math.tex"))

        equations = result.metadata["equations"]
        self.assertEqual(result.metadata["equation_count"], 5)

        # multiline equation from align should produce separate entries
        align_eqs = [e for e in equations if "align" in e["source_location"]]
        self.assertEqual(len(align_eqs), 2)

        self.assertTrue(all("raw" in e and "lhs" in e and "rhs" in e and "source_location" in e for e in equations))


    def test_multiple_equals_splits_on_first_equals(self):
        extractor = MathExtractor()
        tex_path = Path("examples/latex/multi_equals.tex")
        tex_path.write_text("""\\documentclass{article}
\\begin{document}
$u=v=w$
\\end{document}
""")
        try:
            result = extractor.validate(tex_path)
        finally:
            tex_path.unlink(missing_ok=True)

        self.assertEqual(result.metadata["equation_count"], 1)
        eq = result.metadata["equations"][0]
        self.assertEqual(eq["lhs"], "u")
        self.assertEqual(eq["rhs"], "v=w")

    def test_malformed_latex_skips_non_equations(self):
        extractor = MathExtractor()
        result = extractor.validate(Path("examples/latex/malformed_math.tex"))

        # one valid equation from align block only; equation block has no '=' and should be skipped
        self.assertEqual(result.metadata["equation_count"], 1)
        eq = result.metadata["equations"][0]
        self.assertEqual(eq["lhs"], "a")
        self.assertEqual(eq["rhs"], "b + c")

    def test_non_tex_file_fails_validation(self):
        extractor = MathExtractor()
        result = extractor.validate(Path("README.md"))

        self.assertFalse(result.passed)
        self.assertIn("Expected a .tex file", result.errors)


if __name__ == "__main__":
    unittest.main()
