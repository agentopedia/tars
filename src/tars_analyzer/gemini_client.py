from __future__ import annotations

import json
import os
from typing import Any

from .models import (
    Conversation,
    ConversationProgress,
    DimensionScore,
    GeminiEvaluation,
    ProgressionEvaluation,
    TurnDimensionEvaluation,
)


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

    @staticmethod
    def _bounded_score(value: Any, *, min_value: float = 0.0, max_value: float = 10.0) -> float:
        score = float(value)
        if score < min_value or score > max_value:
            raise ValueError(f"Score {score} out of bounds [{min_value}, {max_value}].")
        return score

    def _parse_dimension_score(self, raw: dict[str, Any], *, min_value: float = 0.0, max_value: float = 10.0) -> DimensionScore:
        return DimensionScore(
            score=self._bounded_score(raw["score"], min_value=min_value, max_value=max_value),
            justification=str(raw.get("justification", "")),
            error_flag=(str(raw["error_flag"]) if raw.get("error_flag") else None),
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
  - turn_dimension_scores: array with one item per turn in the same order as the transcript
    each turn item must contain:
      - turn_index: integer
      - role: string
      - content: string
      - helpfulness: {{score, justification, error_flag?}}
      - factual_accuracy: {{score, justification, error_flag?}}
      - instruction_following: {{score, justification, error_flag?}}
      - coherence: {{score, justification, error_flag?}}
      - depth_of_reasoning: {{score, justification, error_flag?}}
      - safety_awareness: {{score, justification, error_flag?}}
      - hallucination_likelihood: {{score, justification, error_flag?}} (0=low risk, 10=high risk)
      - specificity: {{score, justification, error_flag?}}

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
        per_conversation = []
        for item in data.get("per_conversation", []):
            turns = []
            for turn in item.get("turn_dimension_scores", []):
                turns.append(
                    TurnDimensionEvaluation(
                        turn_index=int(turn["turn_index"]),
                        role=str(turn.get("role", "")),
                        content=str(turn.get("content", "")),
                        helpfulness=self._parse_dimension_score(turn["helpfulness"]),
                        factual_accuracy=self._parse_dimension_score(turn["factual_accuracy"]),
                        instruction_following=self._parse_dimension_score(turn["instruction_following"]),
                        coherence=self._parse_dimension_score(turn["coherence"]),
                        depth_of_reasoning=self._parse_dimension_score(turn["depth_of_reasoning"]),
                        safety_awareness=self._parse_dimension_score(turn["safety_awareness"]),
                        hallucination_likelihood=self._parse_dimension_score(turn["hallucination_likelihood"]),
                        specificity=self._parse_dimension_score(turn["specificity"]),
                    )
                )

            per_conversation.append(
                ConversationProgress(
                    conversation_id=str(item["conversation_id"]),
                    rank=int(item["rank"]),
                    overall_agent_quality=self._bounded_score(item["overall_agent_quality"]),
                    improvement_vs_previous=self._bounded_score(
                        item["improvement_vs_previous"], min_value=-5.0, max_value=5.0
                    ),
                    notes=str(item.get("notes", "")),
                    turn_dimension_scores=turns,
                )
            )

        return ProgressionEvaluation(
            overall_summary=str(data.get("overall_summary", "")),
            trajectory_label=str(data.get("trajectory_label", "mixed")),
            trajectory_confidence=self._bounded_score(
                data.get("trajectory_confidence", 0.0)
            ),
            per_conversation=per_conversation,
        )
