from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Turn:
    role: str
    content: str


@dataclass
class Conversation:
    conversation_id: str
    timestamp: datetime
    turns: list[Turn]
    metadata: dict = field(default_factory=dict)


@dataclass
class GeminiEvaluation:
    helpfulness: float
    correctness: float
    proactivity: float
    user_satisfaction: float
    confidence: float
    notes: str


@dataclass
class ConversationProgress:
    conversation_id: str
    rank: int
    overall_agent_quality: float
    improvement_vs_previous: float
    notes: str


@dataclass
class ProgressionEvaluation:
    overall_summary: str
    trajectory_label: str
    trajectory_confidence: float
    per_conversation: list[ConversationProgress]


@dataclass
class ConversationAnalysis:
    conversation_id: str
    timestamp: datetime
    evaluation: GeminiEvaluation
    basic_metrics: dict


__all__ = [
    "Turn",
    "Conversation",
    "GeminiEvaluation",
    "ConversationProgress",
    "ProgressionEvaluation",
    "ConversationAnalysis",
]
