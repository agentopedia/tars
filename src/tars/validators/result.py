from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class ValidationResult:
    name: str
    passed: bool
    status: str | None = None
    reason: str | None = None
    errors: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Return a JSON-serializable representation."""
        return asdict(self)
