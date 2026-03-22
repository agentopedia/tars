from __future__ import annotations

from pathlib import Path
from typing import Any

from tars.validators.base import BaseValidator
from tars.validators.result import ValidationResult

from .extractor import extract_citations
from .resolver import arxiv_exists, doi_resolves


class CitationValidator(BaseValidator):
    """Deterministic citation quality and resolvability validator for LaTeX papers."""

    name = "citation_validator"
    artifact_type = "research-paper"

    def validate(self, artifact_path: Path) -> ValidationResult:
        path = Path(artifact_path)
        if not path.exists():
            return ValidationResult(
                name=self.name,
                passed=False,
                status="FAIL",
                reason="artifact missing",
                errors=[f"Artifact not found: {path}"],
                metadata={"artifact_path": str(path)},
            )

        extraction = extract_citations(path)

        errors: list[str] = []
        warnings: list[str] = []

        missing_keys = sorted(extraction.cite_keys - extraction.bib_keys)
        if missing_keys:
            errors.append(f"In-text citations missing bibliography entries: {', '.join(missing_keys)}")

        malformed_entries: list[str] = []
        doi_checks: list[dict[str, Any]] = []
        arxiv_checks: list[dict[str, Any]] = []

        for entry in extraction.bib_items:
            key = entry.get("key", "")

            required = ["author", "title", "year"]
            missing_required = [f for f in required if not entry.get(f)]
            has_venue = bool(entry.get("journal") or entry.get("booktitle"))
            if missing_required or not has_venue:
                malformed_entries.append(key)
                issues = []
                if missing_required:
                    issues.append(f"missing fields: {', '.join(missing_required)}")
                if not has_venue:
                    issues.append("missing venue (journal/booktitle)")
                warnings.append(f"Malformed bibliography entry '{key}' ({'; '.join(issues)})")

            doi = entry.get("doi", "").strip()
            if doi:
                ok, reason = doi_resolves(doi)
                doi_checks.append({"key": key, "doi": doi, "ok": ok, "reason": reason})
                if not ok:
                    warnings.append(f"DOI check failed for '{key}': {reason}")

            eprint = entry.get("eprint", "").strip()
            archive_prefix = entry.get("archiveprefix", "").strip().lower()
            if eprint and archive_prefix == "arxiv":
                ok, reason = arxiv_exists(eprint)
                arxiv_checks.append({"key": key, "arxiv_id": eprint, "ok": ok, "reason": reason})
                if not ok:
                    warnings.append(f"arXiv check failed for '{key}': {reason}")

        passed = not errors
        status = "PASS" if passed else "FAIL"

        return ValidationResult(
            name=self.name,
            passed=passed,
            status=status,
            reason=None,
            errors=errors,
            metadata={
                "artifact_path": str(path),
                "total_in_text_citations": len(extraction.cite_keys),
                "total_bibliography_entries": len(extraction.bib_keys),
                "missing_citation_keys": missing_keys,
                "malformed_entries": malformed_entries,
                "doi_checks": doi_checks,
                "arxiv_checks": arxiv_checks,
                "warnings": warnings,
            },
        )
