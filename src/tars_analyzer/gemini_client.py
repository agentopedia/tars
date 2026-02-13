from __future__ import annotations

import json
import os
from typing import Any

from .models import Conversation, GeminiEvaluation


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
You are evaluating whether an LLM agent is improving over time.
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
