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
class DimensionScore:
    score: float
    justification: str
    error_flag: str | None = None


@dataclass
class TurnDimensionEvaluation:
    turn_index: int
    role: str
    content: str
    helpfulness: DimensionScore
    factual_accuracy: DimensionScore
    instruction_following: DimensionScore
    coherence: DimensionScore
    depth_of_reasoning: DimensionScore
    safety_awareness: DimensionScore
    hallucination_likelihood: DimensionScore
    specificity: DimensionScore


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
    turn_dimension_scores: list[TurnDimensionEvaluation] = field(default_factory=list)


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
    "DimensionScore",
    "TurnDimensionEvaluation",
    "GeminiEvaluation",
    "ConversationProgress",
    "ProgressionEvaluation",
    "ConversationAnalysis",
]
