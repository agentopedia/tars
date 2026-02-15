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

## Repository contents

- `src/tars_analyzer/models.py` — typed models for conversation structure and progression results.
- `src/tars_analyzer/gemini_client.py` — Gemini client and sequence-level prompt/evaluation logic.
- `src/tars_analyzer/analyzer.py` — JSONL loading, metric aggregation, trend/report generation.
- `src/tars_analyzer/cli.py` — CLI entrypoint (`tars-analyze`).
- `tests/test_analyzer.py` — deterministic progression unit test using a mocked evaluator.
- `examples/conversations.jsonl` — minimal sample input.
- `examples/customer_support_progression.jsonl` — realistic chronological customer-support dataset.
- `notebooks/tars_repo_functionality_test.ipynb` — quick Colab validation notebook.
- `notebooks/tars_real_usecase_colab.ipynb` — real-usecase Colab workflow (offline + optional live Gemini).

## Input format (JSONL)

Each line is one conversation object:

```json
{
  "conversation_id": "session-001",
  "timestamp": "2026-01-05T10:00:00Z",
  "turns": [
    {"role": "human", "content": "..."},
    {"role": "agent", "content": "..."}
  ],
  "metadata": {"optional": "fields"}
}
```

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

## Run analysis

```bash
export GEMINI_API_KEY="your_api_key"
tars-analyze examples/customer_support_progression.jsonl --out output --model gemini-2.0-flash
```

## Report output

The analyzer writes:
- `output/report.json`
- `output/report.md`

`report.json` includes:
- `conversation_count`
- `overall_agent_quality_scores`
- `average_overall_agent_quality`
- `trend_delta_first_to_last`
- `trajectory` (`label`, `confidence`, `summary`)
- `analyses` (per conversation, including basic metrics and progression details)

## Testing

```bash
python -m unittest discover -s tests
```

## Colab notebooks

### 1) Repository functionality notebook
- `notebooks/tars_repo_functionality_test.ipynb`
- Includes install/setup, unit tests, offline mocked progression run, and optional live Gemini run.

### 2) Real use-case notebook
- `notebooks/tars_real_usecase_colab.ipynb`
- Uses `examples/customer_support_progression.jsonl` to test realistic progression behavior.
- Includes:
  - dataset inspection,
  - deterministic offline progression scoring (no API key),
  - optional live Gemini evaluation,
  - progression visualization.
