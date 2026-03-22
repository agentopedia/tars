from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tars.validators.research.citations.citation_validator import CitationValidator
from tars.validators.research.citations.extractor import extract_citations
from tars.validators.research.citations.resolver import arxiv_exists, doi_resolves


class CitationExtractorTests(unittest.TestCase):
    def test_extracts_cites_and_bibitems(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            tex = root / "paper.tex"
            tex.write_text(
                """
                Text with citations \\cite{refA,refB}.
                \\begin{thebibliography}{9}
                \\bibitem{refA} Entry A
                \\bibitem{refB} Entry B
                \\end{thebibliography}
                """,
                encoding="utf-8",
            )
            extraction = extract_citations(tex)

        self.assertEqual({"refA", "refB"}, extraction.cite_keys)
        self.assertEqual({"refA", "refB"}, extraction.bib_keys)

    def test_extracts_compact_bib_entries_and_unquoted_fields(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            tex = root / "paper.tex"
            bib = root / "paper.bib"
            tex.write_text("Text \\cite{refA}.", encoding="utf-8")
            bib.write_text(
                "@article{refA, author={Doe, Jane}, title=\"Compact\", year=2024, journal={J}}",
                encoding="utf-8",
            )

            extraction = extract_citations(tex)

        self.assertEqual({"refA"}, extraction.cite_keys)
        self.assertEqual({"refA"}, extraction.bib_keys)
        self.assertEqual("2024", extraction.bib_items[0]["year"])


class CitationResolverTests(unittest.TestCase):
    def test_doi_malformed(self):
        ok, reason = doi_resolves("not-a-doi")
        self.assertFalse(ok)
        self.assertEqual("Malformed DOI", reason)

    def test_arxiv_malformed(self):
        ok, reason = arxiv_exists("not-an-id")
        self.assertFalse(ok)
        self.assertEqual("Malformed arXiv ID", reason)


class CitationValidatorTests(unittest.TestCase):
    def test_detects_missing_mapping(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            tex = root / "paper.tex"
            tex.write_text(
                """
                Intro \\cite{known,missing}.
                \\begin{thebibliography}{9}
                \\bibitem{known} Known reference
                \\end{thebibliography}
                """,
                encoding="utf-8",
            )

            result = CitationValidator().validate(tex)

        self.assertFalse(result.passed)
        self.assertIn("missing", " ".join(result.errors))

    def test_bib_quality_and_resolvers(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            tex = root / "paper.tex"
            bib = root / "paper.bib"
            tex.write_text("Text \\cite{good,bad}.", encoding="utf-8")
            bib.write_text(
                """
                @article{good,
                  author = {Doe, Jane},
                  title = {A Good Paper},
                  year = {2024},
                  journal = {Journal X},
                  doi = {10.1000/xyz123},
                  archivePrefix = {arXiv},
                  eprint = {1706.03762}
                }
                @article{bad,
                  title = {Missing metadata}
                }
                """,
                encoding="utf-8",
            )

            with patch(
                "tars.validators.research.citations.citation_validator.doi_resolves",
                return_value=(True, None),
            ), patch(
                "tars.validators.research.citations.citation_validator.arxiv_exists",
                return_value=(True, None),
            ):
                result = CitationValidator().validate(tex)

        self.assertTrue(result.passed)
        self.assertIn("bad", result.metadata["malformed_entries"])
        self.assertTrue(result.metadata["warnings"])
        self.assertEqual(1, len(result.metadata["doi_checks"]))
        self.assertEqual(1, len(result.metadata["arxiv_checks"]))


if __name__ == "__main__":
    unittest.main()
