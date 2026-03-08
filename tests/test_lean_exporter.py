from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tars.validators.research.math.lean_exporter import (
    LeanExportValidator,
    equation_to_lean_theorem,
    export_equations_to_lean,
)


class LeanExporterTests(unittest.TestCase):
    def test_equation_to_lean_theorem(self):
        theorem = equation_to_lean_theorem("x^2 + 2*x + 1", "(x+1)^2", 1)
        self.assertIn("theorem eq_1", theorem)
        self.assertIn("=", theorem)
        self.assertIn("sorry", theorem)

    def test_export_equations_to_lean(self):
        content = export_equations_to_lean(
            [
                {
                    "lhs": "x+1",
                    "rhs": "1+x",
                    "raw": "x+1=1+x",
                    "source_location": "line:1:inline",
                }
            ]
        )
        self.assertIn("namespace TarsExport", content)
        self.assertIn("theorem eq_1", content)

    def test_validator_writes_lean_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tex = Path(tmpdir) / "paper.tex"
            tex.write_text(
                "\\begin{equation}\n"
                "x+1=1+x\n"
                "\\end{equation}\n"
            )

            result = LeanExportValidator().validate(tex)
            self.assertTrue(result.passed)
            out = Path(result.metadata["output_path"])
            self.assertTrue(out.exists())
            self.assertIn("theorem eq_1", out.read_text())


if __name__ == "__main__":
    unittest.main()
