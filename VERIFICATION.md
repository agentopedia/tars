# Verification Guide

This file contains verification workflows separated from `README.md`.

## 1) Run unit tests

```bash
python -m unittest discover -s tests
```

## 2) Verify a local `.tex` artifact via validators

```bash
PYTHONPATH=src python - <<'PY'
from pathlib import Path
from dataclasses import asdict
import json

from tars.validators.research.math.math_extractor import MathExtractor
from tars.validators.research.math.math_converter import MathConverter

tex_path = Path('examples/latex/sample_math.tex')
extractor = MathExtractor().validate(tex_path)
converter = MathConverter().validate(tex_path)

print(json.dumps(asdict(extractor), indent=2)[:2000])
print(json.dumps(asdict(converter), indent=2)[:2000])
PY
```

## 3) Verify an arXiv paper URL from CLI (no UI)

Use this when you want to test directly from terminal with a URL like:
`https://arxiv.org/pdf/2603.05469`

```bash
PYTHONPATH=src python - <<'PY'
import json
import tempfile
from dataclasses import asdict
from pathlib import Path

from tars_ui.arxiv import parse_arxiv_id, download_arxiv_source, extract_source_tar, pick_main_tex
from tars.validators.research.math.math_extractor import MathExtractor
from tars.validators.research.math.math_converter import MathConverter

url = 'https://arxiv.org/pdf/2603.05469'
arxiv_id = parse_arxiv_id(url)

with tempfile.TemporaryDirectory() as td:
    base = Path(td)
    tar_path = download_arxiv_source(arxiv_id, base / 'download')
    source_dir = extract_source_tar(tar_path, base / 'src')
    main_tex = pick_main_tex(source_dir)

    extractor = MathExtractor().validate(main_tex)
    converter = MathConverter().validate(main_tex)

    print('main_tex:', main_tex)
    print('expression_count:', extractor.metadata.get('expression_count'))
    print('equation_count:', extractor.metadata.get('equation_count'))
    print('conversion_count:', converter.metadata.get('conversion_count'))

    Path('extractor_result.json').write_text(json.dumps(asdict(extractor), indent=2))
    Path('converter_result.json').write_text(json.dumps(asdict(converter), indent=2))
    print('wrote extractor_result.json and converter_result.json')
PY
```

### Notes
- arXiv verification requires outbound network access to `https://arxiv.org/e-print/<id>`.
- if `latex2sympy2` is not installed, conversion results include structured conversion errors.
