from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from statistics import mean

from .gemini_client import GeminiEvaluator
from .models import Conversation, Turn


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


def analyze_conversations(
    input_path: str | Path,
    output_dir: str | Path,
    model: str = "gemini-2.0-flash",
) -> dict:
    conversations = load_conversations(input_path)
    evaluator = GeminiEvaluator(model=model)

    progression = evaluator.evaluate_progression(conversations)
    by_id = {item.conversation_id: item for item in progression.per_conversation}

    analyses = []
    qualities = []
    for convo in conversations:
        progress = by_id.get(convo.conversation_id)
        analyses.append(
            {
                "conversation_id": convo.conversation_id,
                "timestamp": convo.timestamp.isoformat(),
                "basic_metrics": _basic_metrics(convo),
                "progression": asdict(progress) if progress else None,
            }
        )
        if progress:
            qualities.append(progress.overall_agent_quality)

    first_score = qualities[0] if qualities else 0.0
    last_score = qualities[-1] if qualities else 0.0
    trend_delta = round(last_score - first_score, 3)

    result = {
        "conversation_count": len(conversations),
        "overall_agent_quality_scores": qualities,
        "average_overall_agent_quality": round(mean(qualities), 3) if qualities else 0.0,
        "trend_delta_first_to_last": trend_delta,
        "trajectory": {
            "label": progression.trajectory_label,
            "confidence": progression.trajectory_confidence,
            "summary": progression.overall_summary,
        },
        "analyses": analyses,
    }

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "report.json").write_text(json.dumps(result, indent=2))
    (output_dir / "report.md").write_text(_to_markdown(result))
    return result


def _to_markdown(report: dict) -> str:
    lines = [
        "# Agent Self-Improvement Report",
        "",
        f"- Conversations analyzed: **{report['conversation_count']}**",
        (
            "- Average overall agent quality: "
            f"**{report['average_overall_agent_quality']} / 10**"
        ),
        (
            "- Trajectory: "
            f"**{report['trajectory']['label']}** "
            f"(confidence {report['trajectory']['confidence']})"
        ),
        (
            "- First → Last delta (overall agent quality): "
            f"**{report['trend_delta_first_to_last']:+}**"
        ),
        f"- Summary: {report['trajectory']['summary']}",
        "",
        "## Conversation Breakdown (ordered)",
        "",
    ]

    for item in report["analyses"]:
        progress = item["progression"]
        lines.append(f"### {item['conversation_id']} ({item['timestamp']})")
        if progress:
            lines.extend(
                [
                    f"- Overall agent quality: **{progress['overall_agent_quality']}**",
                    f"- Rank within sequence: **{progress['rank']}**",
                    (
                        "- Improvement vs previous conversation: "
                        f"**{progress['improvement_vs_previous']:+}**"
                    ),
                    f"- Notes: {progress['notes']}",
                ]
            )
        lines.append("")

    return "\n".join(lines)
