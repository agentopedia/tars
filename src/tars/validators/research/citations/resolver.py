from __future__ import annotations

import re
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen

DOI_PATTERN = re.compile(r"^10\.\d{4,9}/[-._;()/:A-Za-z0-9]+$")
ARXIV_PATTERN = re.compile(r"^(\d{4}\.\d{4,5}|[a-z\-]+(\.[A-Z]{2})?/\d{7})(v\d+)?$", re.IGNORECASE)


def doi_resolves(doi: str, timeout: float = 5.0) -> tuple[bool, str | None]:
    if not DOI_PATTERN.match(doi.strip()):
        return False, "Malformed DOI"

    url = f"https://doi.org/{doi.strip()}"
    req = Request(url, method="HEAD", headers={"User-Agent": "TARS-CitationValidator/1.0"})
    try:
        with urlopen(req, timeout=timeout) as resp:  # nosec B310
            code = getattr(resp, "status", 200)
            if 200 <= code < 400:
                return True, None
            return False, f"DOI returned status {code}"
    except HTTPError as exc:
        return False, f"DOI HTTP error: {exc.code}"
    except URLError as exc:
        return False, f"DOI resolution failed: {exc.reason}"


def arxiv_exists(arxiv_id: str, timeout: float = 5.0) -> tuple[bool, str | None]:
    value = arxiv_id.strip()
    if not ARXIV_PATTERN.match(value):
        return False, "Malformed arXiv ID"

    url = f"https://arxiv.org/abs/{value}"
    req = Request(url, method="HEAD", headers={"User-Agent": "TARS-CitationValidator/1.0"})
    try:
        with urlopen(req, timeout=timeout) as resp:  # nosec B310
            code = getattr(resp, "status", 200)
            if 200 <= code < 400:
                return True, None
            return False, f"arXiv returned status {code}"
    except HTTPError as exc:
        return False, f"arXiv HTTP error: {exc.code}"
    except URLError as exc:
        return False, f"arXiv lookup failed: {exc.reason}"
