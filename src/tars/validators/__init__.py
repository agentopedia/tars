"""Deterministic research artifact validator namespace.

This namespace hosts validator interfaces and implementations for paper artifacts
(LaTeX, citations, math, structure, reproducibility).
"""

from .base import ValidationIssue, ValidationResult, Validator

__all__ = ["ValidationIssue", "ValidationResult", "Validator"]
