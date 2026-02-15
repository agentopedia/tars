# TARS Conversation Improvement Analyzer

A Python codebase for analyzing transcript sequences between a human and an LLM agent, using **Gemini** to evaluate whether the **same agent is improving over time** from conversation 1 → 2 → 3, etc.

## What this does

- Loads a time-ordered conversation history from JSONL.
- Sends the **entire ordered sequence** to Gemini for longitudinal evaluation.
- Asks Gemini to rank each conversation by overall agent quality and score change vs. previous conversation.
- Produces:
  - `report.json` (machine-readable)
  - `report.md` (human-readable)
- Reports trajectory (`improving`, `flat`, `declining`, `mixed`) and first-to-last quality delta.

## Project structure

- `src/tars_analyzer/models.py` — data models.
- `src/tars_analyzer/gemini_client.py` — Gemini API integration and progression evaluation.
- `src/tars_analyzer/analyzer.py` — loading, trend logic, and report generation.
- `src/tars_analyzer/cli.py` — CLI entrypoint.
- `tests/test_analyzer.py` — unit test with mocked progression evaluator.
- `examples/conversations.jsonl` — sample input.
- `notebooks/tars_repo_functionality_test.ipynb` — Colab-friendly test flow.

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
