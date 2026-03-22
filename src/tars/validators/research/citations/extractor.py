from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CitationExtraction:
    cite_keys: set[str]
    bib_keys: set[str]
    bib_items: list[dict[str, str]]


_CITE_PATTERN = re.compile(r"\\cite[a-zA-Z*]*\{([^}]*)\}")
_BIBITEM_PATTERN = re.compile(r"\\bibitem\{([^}]*)\}")
_BIB_ENTRY_PATTERN = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,(.*?)\}\s*(?=@|\Z)", re.DOTALL)
_FIELD_PATTERN = re.compile(r"(\w+)\s*=\s*(\{.*?\}|\".*?\"|[^,\n]+)\s*,?", re.DOTALL)


def _split_keys(value: str) -> list[str]:
    return [k.strip() for k in value.split(",") if k.strip()]


def extract_citations(tex_path: Path) -> CitationExtraction:
    text = tex_path.read_text(encoding="utf-8", errors="ignore")

    cite_keys: set[str] = set()
    for m in _CITE_PATTERN.finditer(text):
        cite_keys.update(_split_keys(m.group(1)))

    bib_keys: set[str] = set()
    for m in _BIBITEM_PATTERN.finditer(text):
        bib_keys.add(m.group(1).strip())

    bib_items: list[dict[str, str]] = []
    bib_path = tex_path.with_suffix(".bib")
    if bib_path.exists():
        bib_text = bib_path.read_text(encoding="utf-8", errors="ignore")
        for entry_match in _BIB_ENTRY_PATTERN.finditer(bib_text):
            entry_type = entry_match.group(1).strip().lower()
            key = entry_match.group(2).strip()
            body = entry_match.group(3)
            fields: dict[str, str] = {}
            for field_match in _FIELD_PATTERN.finditer(body):
                fname = field_match.group(1).strip().lower()
                raw_val = field_match.group(2).strip()
                fields[fname] = raw_val.strip("{}\"")
            bib_items.append({"entry_type": entry_type, "key": key, **fields})
            bib_keys.add(key)

    return CitationExtraction(cite_keys=cite_keys, bib_keys=bib_keys, bib_items=bib_items)
