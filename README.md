# TARS Conversation Improvement Analyzer

A Python codebase for analyzing transcripts between a human and an LLM agent, using **Gemini** to score each conversation, then generating a report on whether the agent is improving over time.

## What this does

- Loads conversation history from JSONL.
- Sends each conversation to Gemini for structured evaluation.
- Scores quality dimensions:
  - helpfulness
  - correctness
  - proactivity
  - user satisfaction
  - confidence
- Produces:
  - `report.json` (machine-readable)
  - `report.md` (human-readable)
- Computes trend label (`improving`, `flat`, `declining`) from composite score progression.

## Project structure

- `src/tars_analyzer/models.py` — data models.
- `src/tars_analyzer/gemini_client.py` — Gemini API integration.
- `src/tars_analyzer/analyzer.py` — loading, scoring, trend logic, report generation.
- `src/tars_analyzer/cli.py` — CLI entrypoint.
- `tests/test_analyzer.py` — unit test with mocked Gemini evaluator.
- `examples/conversations.jsonl` — sample input.

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

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
export GEMINI_API_KEY="your_api_key"
tars-analyze examples/conversations.jsonl --out output --model gemini-2.0-flash
```

After running, check:

- `output/report.json`
- `output/report.md`

## Test

```bash
python -m unittest discover -s tests
```

## Colab notebook

A ready-to-run Colab notebook for validating repository functionality is available at:

- `notebooks/tars_repo_functionality_test.ipynb`

It includes install/setup, unit tests, an offline mocked end-to-end run, and an optional live Gemini run.

