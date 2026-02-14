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
class ConversationAnalysis:
    conversation_id: str
    timestamp: datetime
    evaluation: GeminiEvaluation
    basic_metrics: dict
