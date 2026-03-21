from __future__ import annotations

import json
import os
from typing import Any

from tars.validators.result import ValidationResult


class MathValidationSummarizer:
    """Create a human-friendly summary for deterministic math validation results."""

    def __init__(self, model: str = "gemini-2.5-flash") -> None:
        self.model = model

    def summarize(self, result: ValidationResult) -> str:
        fallback = self._fallback_summary(result)

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return fallback

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)
            payload = self._payload(result)
            prompt = (
                "You are a strict math-validation report writer. "
                "Given deterministic validator output, write a concise findings summary "
                "in 2-4 sentences for researchers. "
                "Do not change verdicts or counts. Mention pass/fail/skipped implications.\n\n"
                f"Validator payload:\n{json.dumps(payload, sort_keys=True)}"
            )

            response = client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.1),
            )
            text = (response.text or "").strip()
            return text or fallback
        except Exception:
            return fallback

    @staticmethod
    def _payload(result: ValidationResult) -> dict[str, Any]:
        metrics = result.metadata.get("metrics", {})
        return {
            "status": result.status or ("PASS" if result.passed else "FAIL"),
            "reason": result.reason,
            "error_count": len(result.errors),
            "errors": result.errors,
            "metrics": {
                "total_equations": metrics.get("total_equations", result.metadata.get("equation_count", 0)),
                "validated_equations": metrics.get("validated_equations", 0),
                "failed_equations": metrics.get("failed_equations", 0),
                "skipped_equations": metrics.get("skipped_equations", 0),
            },
        }

    @staticmethod
    def _fallback_summary(result: ValidationResult) -> str:
        metrics = result.metadata.get("metrics", {})
        total = metrics.get("total_equations", result.metadata.get("equation_count", 0))
        validated = metrics.get("validated_equations", 0)
        failed = metrics.get("failed_equations", 0)
        skipped = metrics.get("skipped_equations", 0)
        status = result.status or ("PASS" if result.passed else "FAIL")

        if status == "PASS":
            return (
                f"All checked equations passed deterministic validation. "
                f"Validated {validated} of {total} extracted equations with no failures."
            )

        if status == "SKIPPED":
            return (
                f"Validation was inconclusive for {skipped} equation(s), usually due to conversion limits. "
                f"Only {validated} of {total} equations were validated deterministically."
            )

        return (
            f"Deterministic validation found {failed} failed equation(s) out of {validated} validated "
            f"({total} extracted total). Review reported errors before trusting derivations."
        )
