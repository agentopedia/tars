from __future__ import annotations

from pathlib import Path

from .base import BaseValidator, ValidatorRegistry
from .result import ValidationResult


class ValidationEngine:
    """Orchestrates validator registration, execution, and result aggregation."""

    def __init__(self, registry: ValidatorRegistry | None = None) -> None:
        self.registry = registry or ValidatorRegistry()

    def register_validator(self, validator: BaseValidator) -> None:
        self.registry.register(validator)

    def register_validators(self, validators: list[BaseValidator]) -> None:
        for validator in validators:
            self.register_validator(validator)

    def run(
        self,
        paper_path: str | Path,
        validator_names: list[str] | None = None,
    ) -> list[ValidationResult]:
        artifact = Path(paper_path)
        names = validator_names or self.registry.list_names()
        results: list[ValidationResult] = []
        for name in names:
            results.append(self.registry.validate_with(name, artifact))
        return results

    @staticmethod
    def aggregate(results: list[ValidationResult]) -> dict:
        return {
            "total": len(results),
            "passed": sum(1 for r in results if r.passed),
            "failed": sum(1 for r in results if not r.passed),
            "all_passed": all(r.passed for r in results) if results else True,
        }
