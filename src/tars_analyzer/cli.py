from __future__ import annotations

import argparse

from .analyzer import analyze_conversations


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze ordered LLM-human conversations with Gemini to assess whether the same agent is self-improving over time."
    )
    parser.add_argument("input", help="Path to JSONL conversations file")
    parser.add_argument("--out", default="output", help="Directory for report files")
    parser.add_argument("--model", default="gemini-2.0-flash", help="Gemini model name")
    args = parser.parse_args()

    report = analyze_conversations(args.input, args.out, model=args.model)
    print(
        "Done. "
        f"Trajectory={report['trajectory']['label']} "
        f"first_to_last_delta={report['trend_delta_first_to_last']} "
        f"avg_quality={report['average_overall_agent_quality']}"
    )


if __name__ == "__main__":
    main()
