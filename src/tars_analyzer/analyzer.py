from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from statistics import mean

from .gemini_client import GeminiEvaluator
from .models import Conversation, ConversationAnalysis, Turn


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def load_conversations(path: str | Path) -> list[Conversation]:
    path = Path(path)
    conversations: list[Conversation] = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        data = json.loads(line)
        conversations.append(
            Conversation(
                conversation_id=data["conversation_id"],
                timestamp=_parse_timestamp(data["timestamp"]),
                turns=[Turn(**turn) for turn in data["turns"]],
                metadata=data.get("metadata", {}),
            )
        )
    return sorted(conversations, key=lambda c: c.timestamp)


def _basic_metrics(conversation: Conversation) -> dict:
    agent_turns = [t for t in conversation.turns if t.role.lower() == "agent"]
    user_turns = [t for t in conversation.turns if t.role.lower() == "human"]
    total_tokens_estimate = sum(len(t.content.split()) for t in conversation.turns)
    return {
        "agent_turn_count": len(agent_turns),
        "human_turn_count": len(user_turns),
        "avg_agent_words": mean([len(t.content.split()) for t in agent_turns])
        if agent_turns
        else 0.0,
        "total_words": total_tokens_estimate,
    }


def _composite_score(analysis: ConversationAnalysis) -> float:
    ev = analysis.evaluation
    return round(
        (ev.helpfulness + ev.correctness + ev.proactivity + ev.user_satisfaction) / 4, 3
    )


def analyze_conversations(
    input_path: str | Path,
    output_dir: str | Path,
    model: str = "gemini-2.0-flash",
) -> dict:
    conversations = load_conversations(input_path)
    evaluator = GeminiEvaluator(model=model)
    analyses: list[ConversationAnalysis] = []

    for convo in conversations:
        evaluation = evaluator.evaluate(convo)
        analyses.append(
            ConversationAnalysis(
                conversation_id=convo.conversation_id,
                timestamp=convo.timestamp,
                evaluation=evaluation,
                basic_metrics=_basic_metrics(convo),
            )
        )

    scores = [_composite_score(a) for a in analyses]
    trend = scores[-1] - scores[0] if len(scores) > 1 else 0.0
    trend_label = "improving" if trend > 0.2 else "declining" if trend < -0.2 else "flat"

    result = {
        "conversation_count": len(analyses),
        "scores": scores,
        "average_score": round(mean(scores), 3) if scores else 0.0,
        "trend_delta": round(trend, 3),
        "trend_label": trend_label,
        "analyses": [
            {
                "conversation_id": a.conversation_id,
                "timestamp": a.timestamp.isoformat(),
                "evaluation": asdict(a.evaluation),
                "basic_metrics": a.basic_metrics,
                "composite_score": _composite_score(a),
            }
            for a in analyses
        ],
    }

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "report.json").write_text(json.dumps(result, indent=2))
    (output_dir / "report.md").write_text(_to_markdown(result))
    return result


def _to_markdown(report: dict) -> str:
    lines = [
        "# Agent Improvement Report",
        "",
        f"- Conversations analyzed: **{report['conversation_count']}**",
        f"- Average composite score: **{report['average_score']} / 10**",
        f"- Trend: **{report['trend_label']}** (delta {report['trend_delta']:+})",
        "",
        "## Conversation Breakdown",
        "",
    ]

    for item in report["analyses"]:
        ev = item["evaluation"]
        lines.extend(
            [
                f"### {item['conversation_id']} ({item['timestamp']})",
                f"- Composite: **{item['composite_score']}**",
                (
                    f"- Scores → helpfulness {ev['helpfulness']}, correctness {ev['correctness']}, "
                    f"proactivity {ev['proactivity']}, user_satisfaction {ev['user_satisfaction']}"
                ),
                f"- Confidence: {ev['confidence']}",
                f"- Notes: {ev['notes']}",
                "",
            ]
        )
    return "\n".join(lines)
