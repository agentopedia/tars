# 🚀 TARS Toolkit

> 🧠 **Analyze conversation improvement** + 📐 **validate research math** in one practical toolkit.

TARS is a Python toolkit for two core workflows:

1. 🤖 **Conversation progression analysis** for ordered human↔agent conversations.
2. 📄 **Deterministic research-math validation** for LaTeX papers.

It includes CLIs, a lightweight local UI for arXiv sources, example artifacts, and a full unit test suite. ✅

---

## ✨ Features

### 1) 🤖 Conversation progression analyzer (`tars_analyzer`)

- 📥 Loads ordered JSONL conversations
- 🧪 Evaluates progression with Gemini (`GeminiEvaluator`) or deterministic test doubles
- 📝 Produces:
  - `report.json`
  - `report.md`
- 📈 Computes trajectory labels such as `improving`, `flat`, `declining`, `mixed`

### 2) 🧩 Validator framework (`tars.validators`)

Core framework:

- 🧱 `BaseValidator`
- 🗂️ `ValidatorRegistry`
- ⚙️ `ValidationEngine`
- 📦 `ValidationResult`

Research math validators:

- 🔎 `MathExtractor` — extract display/inline equations from `.tex`
- 🔄 `MathConverter` — normalize LaTeX and convert to SymPy (`latex2sympy2`)
- 🧠 `SymbolicValidator` — symbolic equivalence checks
- 🎯 `NumericValidator` — numeric fallback checks via randomized substitution
- 🧭 `MathValidator` — orchestrates extraction → conversion → symbolic → numeric fallback with metrics
- 📏 `DimensionalValidator` — Pint-based dimensional consistency checks
- 🧪 `LeanExportValidator` — exports equations as Lean theorem skeletons (`.lean`) for future formal proof workflows

### 3) 💻 CLI + 🌐 UI

- `tars-analyze` — run conversation progression analysis
- `tars validate-math <paper.tex>` — run math validation pipeline with summary output
- `tars-ui` — local web UI for arXiv source-based validation (`http://localhost:8000`)

### 4) 📚 Examples + notebooks

- 💬 Conversation datasets in `examples/*.jsonl`
- 🧾 LaTeX samples in:
  - `examples/latex/`
  - `examples/research/` (✅ valid + ❌ invalid research-style equations)
- 📓 Notebooks in `notebooks/` for offline and optional live Gemini runs

---

## 🛠️ Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

Dependencies include:

- `google-genai`
- `sympy`
- `latex2sympy2`
- `pint`

---

## ⚡ Quickstart

### A) 🤖 Conversation analysis

```bash
export GEMINI_API_KEY="your_api_key"
tars-analyze examples/customer_support_progression.jsonl --out output --model gemini-2.0-flash
```

### B) 📐 Math validation from CLI

```bash
tars validate-math examples/research/math_valid.tex
```

Try the invalid sample too:

```bash
tars validate-math examples/research/math_invalid.tex
```

### C) 🌐 Local arXiv UI

```bash
tars-ui
```

Then open 👉 `http://localhost:8000`.

---

## 🗺️ Package layout

- `src/tars_analyzer/` — analyzer package and `tars-analyze` CLI
- `src/tars/validators/` — validator framework and research validators
- `src/tars_ui/` — arXiv utilities + local web UI
- `examples/` — conversation + LaTeX samples
- `tests/` — unit and integration tests

---

## ✅ Testing

Run all tests:

```bash
python -m unittest discover -s tests
```

Notes:

- ⚠️ Some tests are dependency-guarded and skipped if optional runtime packages are missing
- 🧪 The suite covers analyzer behavior, validator orchestration, extractor/converter/symbolic/numeric/dimensional validation, Lean export, arXiv utils, and CLI flows

---

## 🔍 Verification guide

For step-by-step verification workflows (including arXiv URL-based checks), see:

- `VERIFICATION.md`
