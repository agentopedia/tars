from __future__ import annotations

import argparse

from .analyzer import analyze_conversations


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze LLM-human conversations with Gemini and detect improvement trends."
    )
    parser.add_argument("input", help="Path to JSONL conversations file")
    parser.add_argument("--out", default="output", help="Directory for report files")
    parser.add_argument("--model", default="gemini-2.0-flash", help="Gemini model name")
    args = parser.parse_args()

    report = analyze_conversations(args.input, args.out, model=args.model)
    print(
        f"Done. Trend={report['trend_label']} delta={report['trend_delta']} "
        f"avg={report['average_score']}"
    )


if __name__ == "__main__":
    main()
