from __future__ import annotations

import html
import json
import tempfile
import urllib.parse
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from tars.validators.research.math.math_converter import MathConverter
from tars.validators.research.math.math_extractor import MathExtractor
from tars_ui.arxiv import download_arxiv_source, extract_source_tar, parse_arxiv_id, pick_main_tex


class TarsUIHandler(BaseHTTPRequestHandler):
    def _render(self, *, arxiv_url: str = "", error: str | None = None, result: dict | None = None) -> bytes:
        error_html = f"<p style='color:#b00020;font-weight:bold'>{html.escape(error)}</p>" if error else ""
        result_html = ""
        if result:
            result_html = f"""
            <h2>Selected Main TeX</h2>
            <p><code>{html.escape(result['main_tex'])}</code></p>
            <h2>Math Extractor Result</h2>
            <pre>{html.escape(result['extractor_json'])}</pre>
            <h2>Math Converter Result</h2>
            <pre>{html.escape(result['converter_json'])}</pre>
            """

        body = f"""
        <!doctype html>
        <html>
        <head>
          <meta charset="utf-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1" />
          <title>TARS Validator UI</title>
          <style>
            body {{ font-family: Arial, sans-serif; margin: 2rem; }}
            input {{ width: 460px; padding: .6rem; }}
            button {{ padding: .6rem 1rem; }}
            pre {{ background: #111; color: #eee; padding: 1rem; border-radius: 8px; overflow: auto; }}
          </style>
        </head>
        <body>
          <h1>TARS Research Paper Validator</h1>
          <p>Paste an arXiv URL (or ID) to run existing math extraction/conversion validators.</p>
          <form method="post">
            <input type="text" name="arxiv_url" required placeholder="https://arxiv.org/abs/1706.03762" value="{html.escape(arxiv_url)}"/>
            <button type="submit">Validate</button>
          </form>
          {error_html}
          {result_html}
        </body>
        </html>
        """
        return body.encode("utf-8")

    def do_GET(self):  # noqa: N802
        data = self._render()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        form = urllib.parse.parse_qs(raw)
        arxiv_url = form.get("arxiv_url", [""])[0].strip()

        error = None
        result = None
        try:
            arxiv_id = parse_arxiv_id(arxiv_url)
            with tempfile.TemporaryDirectory() as td:
                base = Path(td)
                tar_path = download_arxiv_source(arxiv_id, base / "download")
                source_dir = extract_source_tar(tar_path, base / "src")
                main_tex = pick_main_tex(source_dir)

                extractor_result = MathExtractor().validate(main_tex)
                converter_result = MathConverter().validate(main_tex)

                result = {
                    "main_tex": str(main_tex),
                    "extractor_json": json.dumps(asdict(extractor_result), indent=2),
                    "converter_json": json.dumps(asdict(converter_result), indent=2),
                }
        except Exception as exc:  # pragma: no cover - UI path
            error = str(exc)

        data = self._render(arxiv_url=arxiv_url, error=error, result=result)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", 8000), TarsUIHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()
