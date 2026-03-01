"""Deterministic research artifact validator namespace.

This namespace hosts validator interfaces and implementations for paper artifacts
(LaTeX, citations, math, structure, reproducibility).
"""

from .base import BaseValidator, ValidatorRegistry
from .result import ValidationResult

__all__ = ["ValidationResult", "BaseValidator", "ValidatorRegistry"]
