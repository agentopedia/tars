from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from .result import ValidationResult


class BaseValidator(ABC):
    """Base class for validator plugins.

    Concrete validators should define a unique `name` and optional `artifact_type`
    and implement `validate`.
    """

    name: str
    artifact_type: str = "generic"

    @abstractmethod
    def validate(self, artifact_path: Path) -> ValidationResult:
        """Validate an artifact and return a standardized ValidationResult."""
        raise NotImplementedError


class ValidatorRegistry:
    """In-memory plugin registry for validator implementations."""

    def __init__(self) -> None:
        self._validators: dict[str, BaseValidator] = {}

    def register(self, validator: BaseValidator) -> None:
        if not validator.name:
            raise ValueError("Validator name must be non-empty.")
        self._validators[validator.name] = validator

    def get(self, name: str) -> BaseValidator:
        if name not in self._validators:
            raise KeyError(f"Validator '{name}' is not registered.")
        return self._validators[name]

    def list_names(self) -> list[str]:
        return sorted(self._validators.keys())

    def validate_with(self, name: str, artifact_path: Path) -> ValidationResult:
        validator = self.get(name)
        return validator.validate(artifact_path)
