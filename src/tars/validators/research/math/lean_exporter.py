from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re

from tars.validators.base import BaseValidator
from tars.validators.result import ValidationResult

from .math_extractor import MathExtractor


@dataclass
class LeanEquation:
    source_location: str
    raw: str
    lean_theorem: str


def _latex_to_lean(expr: str) -> str:
    text = expr.strip()
    text = text.replace(r"\cdot", "*")
    text = text.replace(r"\times", "*")
    text = text.replace("{", "(").replace("}", ")")

    text = re.sub(r"\\sin\s*\((.*?)\)", r"Real.sin (\1)", text)
    text = re.sub(r"\\cos\s*\((.*?)\)", r"Real.cos (\1)", text)
    text = re.sub(r"\\log\s*\((.*?)\)", r"Real.log (\1)", text)
    text = re.sub(r"\\exp\s*\((.*?)\)", r"Real.exp (\1)", text)

    # Simple fraction normalization: \frac(a)(b) -> ((a) / (b))
    frac_pattern = re.compile(r"\\frac\s*\(([^()]+)\)\s*\(([^()]+)\)")
    while True:
        updated = frac_pattern.sub(r"((\1) / (\2))", text)
        if updated == text:
            break
        text = updated

    text = re.sub(r"\s+", " ", text).strip()
    return text


def equation_to_lean_theorem(lhs: str, rhs: str, index: int) -> str:
    lhs_lean = _latex_to_lean(lhs)
    rhs_lean = _latex_to_lean(rhs)
    return (
        f"theorem eq_{index} : {lhs_lean} = {rhs_lean} := by\n"
        "  sorry"
    )


def export_equations_to_lean(equations: list[dict]) -> str:
    lines = ["import Mathlib", "", "namespace TarsExport", ""]
    for i, eq in enumerate(equations, start=1):
        lines.append(f"-- {eq['source_location']}: {eq['raw']}")
        lines.append(equation_to_lean_theorem(eq["lhs"], eq["rhs"], i))
        lines.append("")
    lines.append("end TarsExport")
    return "\n".join(lines).strip() + "\n"


class LeanExportValidator(BaseValidator):
    """Export extracted equations to Lean theorem skeletons for future proof work."""

    name = "lean_exporter"
    artifact_type = "research-paper"

    def __init__(self) -> None:
        self.extractor = MathExtractor()

    def validate(self, artifact_path: Path) -> ValidationResult:
        extraction = self.extractor.validate(artifact_path)
        if not extraction.passed:
            return ValidationResult(
                name=self.name,
                passed=False,
                status="FAIL",
                reason="extraction failure",
                errors=extraction.errors,
                metadata={"artifact_path": str(artifact_path), "output_path": None, "equations": []},
            )

        equations = extraction.metadata.get("equations", [])
        lean_content = export_equations_to_lean(equations)
        output_path = Path(artifact_path).with_suffix(".lean")
        output_path.write_text(lean_content)

        exported: list[dict] = []
        for i, eq in enumerate(equations, start=1):
            exported.append(
                asdict(
                    LeanEquation(
                        source_location=eq["source_location"],
                        raw=eq["raw"],
                        lean_theorem=equation_to_lean_theorem(eq["lhs"], eq["rhs"], i),
                    )
                )
            )

        return ValidationResult(
            name=self.name,
            passed=True,
            status="PASS",
            errors=[],
            metadata={
                "artifact_path": str(artifact_path),
                "output_path": str(output_path),
                "equation_count": len(equations),
                "equations": exported,
            },
        )
