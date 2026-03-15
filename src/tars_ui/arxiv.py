from __future__ import annotations

import re
import tarfile
import urllib.request
from pathlib import Path


def parse_arxiv_id(url_or_id: str) -> str:
    value = url_or_id.strip()
    if value.startswith("http"):
        m = re.search(r"arxiv\.org/(abs|pdf)/([^?#]+)", value)
        if not m:
            raise ValueError("Invalid arXiv URL")
        arxiv_id = m.group(2)
        arxiv_id = arxiv_id.removesuffix(".pdf")
        return arxiv_id
    return value


def download_arxiv_source(arxiv_id: str, destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    tar_path = destination / "source.tar"
    url = f"https://arxiv.org/e-print/{arxiv_id}"
    urllib.request.urlretrieve(url, tar_path)
    return tar_path


def extract_source_tar(tar_path: Path, destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(tar_path) as tf:
        tf.extractall(destination)
    return destination


def pick_main_tex(source_dir: Path) -> Path:
    tex_files = list(source_dir.rglob("*.tex"))
    if not tex_files:
        raise FileNotFoundError("No .tex files found in arXiv source")
    return max(tex_files, key=lambda p: p.stat().st_size)
