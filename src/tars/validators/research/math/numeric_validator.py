from __future__ import annotations

import random
from pathlib import Path
from typing import Any

from tars.validators.base import BaseValidator
from tars.validators.result import ValidationResult


class NumericValidator(BaseValidator):
    """Numerically validate symbolic equivalence via randomized substitution.

    For each trial, random numeric values are sampled for all free symbols,
    both expressions are evaluated, and numeric values are compared within a
    tolerance. Domain-invalid samples (e.g. division by zero) are skipped and
    resampled.
    """

    name = "numeric_validator"
    artifact_type = "research-paper"

    @staticmethod
    def _sample_value(rng: random.Random, *, positive_only: bool, avoid_zero: bool) -> float:
        """Sample one numeric value with simple domain controls."""
        while True:
            value = rng.uniform(0.1, 5.0) if positive_only else rng.uniform(-5.0, 5.0)
            if avoid_zero and abs(value) < 1e-6:
                continue
            return value

    @staticmethod
    def _is_close(lhs_val: complex, rhs_val: complex, tolerance: float) -> bool:
        return abs(lhs_val - rhs_val) <= tolerance

    def validate_equivalence(
        self,
        lhs_sympy: Any,
        rhs_sympy: Any,
        *,
        trials: int = 10,
        tolerance: float = 1e-6,
        seed: int = 0,
        max_resample_attempts: int = 50,
    ) -> ValidationResult:
        """Validate `lhs_sympy == rhs_sympy` numerically over randomized trials."""
        try:
            import sympy as sp  # type: ignore
        except Exception as exc:
            return ValidationResult(
                name=self.name,
                passed=False,
                errors=[f"SymPy is not available: {exc}"],
                metadata={"lhs": str(lhs_sympy), "rhs": str(rhs_sympy)},
            )

        rng = random.Random(seed)
        symbols = sorted(lhs_sympy.free_symbols.union(rhs_sympy.free_symbols), key=lambda s: s.name)
        denom_symbols = set(sp.denom(sp.together(lhs_sympy)).free_symbols).union(
            sp.denom(sp.together(rhs_sympy)).free_symbols
        )

        successful_trials = 0
        for trial in range(trials):
            evaluated = False
            for _ in range(max_resample_attempts):
                substitution = {
                    symbol: self._sample_value(
                        rng,
                        positive_only=bool(getattr(symbol, "is_positive", False)),
                        avoid_zero=(symbol in denom_symbols),
                    )
                    for symbol in symbols
                }

                try:
                    lhs_eval = lhs_sympy.subs(substitution).evalf()
                    rhs_eval = rhs_sympy.subs(substitution).evalf()
                except Exception:
                    continue

                if (
                    lhs_eval in (sp.zoo, sp.oo, -sp.oo, sp.nan)
                    or rhs_eval in (sp.zoo, sp.oo, -sp.oo, sp.nan)
                ):
                    continue

                try:
                    lhs_val = complex(lhs_eval)
                    rhs_val = complex(rhs_eval)
                except Exception:
                    continue

                evaluated = True
                if not self._is_close(lhs_val, rhs_val, tolerance):
                    return ValidationResult(
                        name=self.name,
                        passed=False,
                        errors=["Numeric mismatch detected"],
                        metadata={
                            "lhs": str(lhs_sympy),
                            "rhs": str(rhs_sympy),
                            "trial": trial,
                            "substitution": {str(k): float(v) for k, v in substitution.items()},
                            "lhs_value": [lhs_val.real, lhs_val.imag],
                            "rhs_value": [rhs_val.real, rhs_val.imag],
                            "tolerance": tolerance,
                        },
                    )

                successful_trials += 1
                break

            if not evaluated:
                return ValidationResult(
                    name=self.name,
                    passed=False,
                    errors=["Unable to find a safe numeric sample for evaluation"],
                    metadata={
                        "lhs": str(lhs_sympy),
                        "rhs": str(rhs_sympy),
                        "trial": trial,
                        "max_resample_attempts": max_resample_attempts,
                    },
                )

        return ValidationResult(
            name=self.name,
            passed=True,
            errors=[],
            metadata={
                "lhs": str(lhs_sympy),
                "rhs": str(rhs_sympy),
                "trials": trials,
                "successful_trials": successful_trials,
                "tolerance": tolerance,
            },
        )

    def validate(self, artifact_path: Path) -> ValidationResult:
        """Path-based validation is not implemented for this validator stage."""
        return ValidationResult(
            name=self.name,
            passed=False,
            errors=[
                "Path-based numeric validation is not implemented. "
                "Use validate_equivalence(lhs_sympy, rhs_sympy)."
            ],
            metadata={"artifact_path": str(artifact_path)},
        )
