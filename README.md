# TARS Conversation Improvement Analyzer

Analyze whether the **same LLM agent is improving over time** across an ordered sequence of human↔agent conversations using Gemini.

## Overview

This repo evaluates longitudinal agent quality (conversation 1 → 2 → 3 → ...), not just isolated single-chat quality.

Given JSONL conversations ordered by timestamp, the analyzer:
- sends the sequence to Gemini for progression scoring,
- captures per-conversation quality and rank,
- computes first-to-last quality delta,
- labels overall trajectory as `improving`, `flat`, `declining`, or `mixed`,
- generates both JSON and Markdown reports.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

### Run conversation analysis

```bash
export GEMINI_API_KEY="your_api_key"
tars-analyze examples/customer_support_progression.jsonl --out output --model gemini-2.0-flash
```

### Run arXiv validator UI

```bash
tars-ui
```

Open `http://localhost:8000` and provide an arXiv URL/ID.

## Core modules

- `src/tars_analyzer/` — conversation progression analyzer package.
- `src/tars/validators/` — deterministic validator framework + research/math validators.
- `src/tars_ui/` — local web UI and arXiv download helpers.

## Verification and testing

Detailed verification flows (including **CLI verification with arXiv URL**) are in:

- `VERIFICATION.md`

For quick test run:

```bash
python -m unittest discover -s tests
```
