from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tars_ui.arxiv import parse_arxiv_id, pick_main_tex


class ArxivUtilsTests(unittest.TestCase):
    def test_parse_arxiv_id(self):
        self.assertEqual(parse_arxiv_id("https://arxiv.org/abs/1706.03762"), "1706.03762")
        self.assertEqual(parse_arxiv_id("https://arxiv.org/pdf/1706.03762.pdf"), "1706.03762")
        self.assertEqual(parse_arxiv_id("2401.12345"), "2401.12345")

    def test_pick_main_tex_selects_largest(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            a = d / "a.tex"
            b = d / "b.tex"
            a.write_text("short")
            b.write_text("this is much longer content")
            self.assertEqual(pick_main_tex(d), b)


if __name__ == "__main__":
    unittest.main()
