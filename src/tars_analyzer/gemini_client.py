from __future__ import annotations

import json
import os
from typing import Any

from .models import Conversation, ConversationProgress, GeminiEvaluation, ProgressionEvaluation


class GeminiEvaluator:
    def __init__(self, model: str = "gemini-2.0-flash") -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set.")
        from google import genai  # lazy import for easier local testing

        self._types = __import__("google.genai.types", fromlist=["GenerateContentConfig"])
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def evaluate(self, conversation: Conversation) -> GeminiEvaluation:
        transcript = "\n".join(
            f"{turn.role.upper()}: {turn.content}" for turn in conversation.turns
        )

        prompt = f"""
Score this single conversation.
Return STRICT JSON with keys:
helpfulness, correctness, proactivity, user_satisfaction, confidence, notes.
Scores are 0-10 floats.

Conversation transcript:
{transcript}
""".strip()

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=self._types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1,
            ),
        )

        data: dict[str, Any] = json.loads(response.text)
        return GeminiEvaluation(
            helpfulness=float(data["helpfulness"]),
            correctness=float(data["correctness"]),
            proactivity=float(data["proactivity"]),
            user_satisfaction=float(data["user_satisfaction"]),
            confidence=float(data["confidence"]),
            notes=str(data.get("notes", "")),
        )

    def evaluate_progression(self, conversations: list[Conversation]) -> ProgressionEvaluation:
        ordered = sorted(conversations, key=lambda c: c.timestamp)
        blocks = []
        for i, convo in enumerate(ordered, start=1):
            transcript = "\n".join(
                f"{turn.role.upper()}: {turn.content}" for turn in convo.turns
            )
            blocks.append(
                f"Conversation #{i} | id={convo.conversation_id} | timestamp={convo.timestamp.isoformat()}\n{transcript}"
            )

        conversation_block = "\n\n".join(blocks)
        prompt = f"""
You are evaluating the SELF-IMPROVING NATURE of one agent across a sequence of conversations.
Important: this is a longitudinal ranking task.
Given ordered conversations from earliest to latest, decide whether the agent improves over time.

Return STRICT JSON with keys:
- overall_summary: string
- trajectory_label: one of ["improving", "flat", "declining", "mixed"]
- trajectory_confidence: float from 0 to 10
- per_conversation: array of objects with keys:
  - conversation_id: string
  - rank: integer (1 = weakest overall agent quality in the sequence, N = strongest)
  - overall_agent_quality: float 0-10
  - improvement_vs_previous: float in [-5, 5] (0 for the first conversation)
  - notes: short string explaining why this item is stronger/weaker

Conversations (ordered by time):
{conversation_block}
""".strip()

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=self._types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1,
            ),
        )

        data: dict[str, Any] = json.loads(response.text)
        per_conversation = [
            ConversationProgress(
                conversation_id=str(item["conversation_id"]),
                rank=int(item["rank"]),
                overall_agent_quality=float(item["overall_agent_quality"]),
                improvement_vs_previous=float(item["improvement_vs_previous"]),
                notes=str(item.get("notes", "")),
            )
            for item in data.get("per_conversation", [])
        ]

        return ProgressionEvaluation(
            overall_summary=str(data.get("overall_summary", "")),
            trajectory_label=str(data.get("trajectory_label", "mixed")),
            trajectory_confidence=float(data.get("trajectory_confidence", 0.0)),
            per_conversation=per_conversation,
        )
