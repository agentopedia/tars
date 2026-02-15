from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tars_analyzer import analyzer
from tars_analyzer.models import ConversationProgress, ProgressionEvaluation


class FakeEvaluator:
    def __init__(self, model: str = "gemini-2.0-flash") -> None:
        self.model = model

    def evaluate_progression(self, conversations):
        ordered = sorted(conversations, key=lambda c: c.timestamp)
        items = []
        for idx, convo in enumerate(ordered):
            items.append(
                ConversationProgress(
                    conversation_id=convo.conversation_id,
                    rank=idx + 1,
                    overall_agent_quality=6.0 + idx,
                    improvement_vs_previous=0.0 if idx == 0 else 1.0,
                    notes="synthetic progression",
                )
            )
        return ProgressionEvaluation(
            overall_summary="Agent gets better in each conversation.",
            trajectory_label="improving",
            trajectory_confidence=9.0,
            per_conversation=items,
        )


class AnalyzerTests(unittest.TestCase):
    def test_progression_improving(self):
        raw = "\n".join(
            [
                json.dumps(
                    {
                        "conversation_id": "conv-0",
                        "timestamp": "2025-01-01T00:00:00Z",
                        "turns": [
                            {"role": "human", "content": "help"},
                            {"role": "agent", "content": "basic reply"},
                        ],
                    }
                ),
                json.dumps(
                    {
                        "conversation_id": "conv-1",
                        "timestamp": "2025-01-02T00:00:00Z",
                        "turns": [
                            {"role": "human", "content": "help"},
                            {"role": "agent", "content": "better response"},
                        ],
                    }
                ),
                json.dumps(
                    {
                        "conversation_id": "conv-2",
                        "timestamp": "2025-01-03T00:00:00Z",
                        "turns": [
                            {"role": "human", "content": "help"},
                            {"role": "agent", "content": "best response"},
                        ],
                    }
                ),
            ]
        )

        with tempfile.TemporaryDirectory() as td:
            input_path = Path(td) / "conversations.jsonl"
            out_dir = Path(td) / "out"
            input_path.write_text(raw)

            original = analyzer.GeminiEvaluator
            analyzer.GeminiEvaluator = FakeEvaluator
            try:
                report = analyzer.analyze_conversations(input_path, out_dir)
            finally:
                analyzer.GeminiEvaluator = original

            self.assertEqual(report["trajectory"]["label"], "improving")
            self.assertEqual(report["trend_delta_first_to_last"], 2.0)
            self.assertTrue((out_dir / "report.md").exists())
            self.assertTrue((out_dir / "report.json").exists())


if __name__ == "__main__":
    unittest.main()
