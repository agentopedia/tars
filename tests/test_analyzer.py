from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tars_analyzer import analyzer
from tars_analyzer.models import GeminiEvaluation


class FakeEvaluator:
    def __init__(self, model: str = "gemini-2.0-flash") -> None:
        self.model = model

    def evaluate(self, conversation):
        idx = int(conversation.conversation_id.split("-")[-1])
        base = 5 + idx
        return GeminiEvaluation(
            helpfulness=base,
            correctness=base,
            proactivity=base,
            user_satisfaction=base,
            confidence=8.0,
            notes="synthetic",
        )


class AnalyzerTests(unittest.TestCase):
    def test_trend_improving(self):
        raw = "\n".join(
            [
                json.dumps(
                    {
                        "conversation_id": "conv-0",
                        "timestamp": "2025-01-01T00:00:00Z",
                        "turns": [
                            {"role": "human", "content": "help"},
                            {"role": "agent", "content": "sure"},
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

            self.assertEqual(report["trend_label"], "improving")
            self.assertTrue((out_dir / "report.md").exists())


if __name__ == "__main__":
    unittest.main()
