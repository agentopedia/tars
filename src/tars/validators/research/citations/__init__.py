"""Citation validation helpers and validator implementation."""

from .citation_validator import CitationValidator
from .extractor import CitationExtraction, extract_citations
from .resolver import arxiv_exists, doi_resolves

__all__ = [
    "CitationValidator",
    "CitationExtraction",
    "extract_citations",
    "doi_resolves",
    "arxiv_exists",
]
