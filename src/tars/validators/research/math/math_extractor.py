from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path

from tars.validators.base import BaseValidator
from tars.validators.result import ValidationResult


@dataclass
class ExtractedMathExpression:
    """Structured LaTeX math expression extracted from a .tex artifact."""

    raw_latex: str
    line_number: int
    environment_type: str


@dataclass
class Equation:
    """Normalized equation split into left/right sides when '=' is present."""

    raw: str
    lhs: str
    rhs: str
    source_location: str


class MathExtractor(BaseValidator):
    """Extract and normalize LaTeX math expressions from .tex files.

    Supported environment types:
    - display_brackets: `\\[ ... \\]`
    - equation: `\\begin{equation} ... \\end{equation}`
    - align: `\\begin{align} ... \\end{align}`
    - inline: `$...$`

    Extraction is robust to multiline display/equation/align blocks and records
    source line numbers for each match.
    """

    name = "math_extractor"
    artifact_type = "research-paper"

    _BLOCK_PATTERNS = [
        ("display_brackets", re.compile(r"\\\[(.*?)\\\]", re.DOTALL)),
        (
            "equation",
            re.compile(r"\\begin\{equation\}(.*?)\\end\{equation\}", re.DOTALL),
        ),
        ("align", re.compile(r"\\begin\{align\}(.*?)\\end\{align\}", re.DOTALL)),
    ]

    @staticmethod
    def _line_number(text: str, index: int) -> int:
        return text.count("\n", 0, index) + 1

    def _extract_blocks(self, text: str) -> tuple[list[ExtractedMathExpression], list[tuple[int, int]]]:
        expressions: list[ExtractedMathExpression] = []
        consumed_spans: list[tuple[int, int]] = []

        for env_type, pattern in self._BLOCK_PATTERNS:
            for match in pattern.finditer(text):
                raw = match.group(0)
                start, end = match.span()
                expressions.append(
                    ExtractedMathExpression(
                        raw_latex=raw,
                        line_number=self._line_number(text, start),
                        environment_type=env_type,
                    )
                )
                consumed_spans.append((start, end))
        return expressions, consumed_spans

    @staticmethod
    def _inside_spans(pos: int, spans: list[tuple[int, int]]) -> bool:
        return any(start <= pos < end for start, end in spans)

    def _extract_inline(self, text: str, consumed_spans: list[tuple[int, int]]) -> list[ExtractedMathExpression]:
        expressions: list[ExtractedMathExpression] = []
        i = 0
        n = len(text)

        while i < n:
            if text[i] != "$" or self._inside_spans(i, consumed_spans):
                i += 1
                continue

            if i > 0 and text[i - 1] == "\\":
                i += 1
                continue

            if i + 1 < n and text[i + 1] == "$":
                i += 2
                continue

            start = i
            i += 1
            while i < n:
                if self._inside_spans(i, consumed_spans):
                    i += 1
                    continue
                if text[i] == "$" and not (i > 0 and text[i - 1] == "\\"):
                    raw = text[start : i + 1]
                    expressions.append(
                        ExtractedMathExpression(
                            raw_latex=raw,
                            line_number=self._line_number(text, start),
                            environment_type="inline",
                        )
                    )
                    i += 1
                    break
                i += 1

        return expressions

    @staticmethod
    def _strip_delimiters(raw_latex: str, environment_type: str) -> str:
        text = raw_latex.strip()
        if environment_type == "inline" and text.startswith("$") and text.endswith("$"):
            return text[1:-1].strip()
        if environment_type == "display_brackets":
            text = re.sub(r"^\\\[", "", text)
            text = re.sub(r"\\\]$", "", text)
            return text.strip()
        if environment_type == "equation":
            text = re.sub(r"^\\begin\{equation\}", "", text)
            text = re.sub(r"\\end\{equation\}$", "", text)
            return text.strip()
        if environment_type == "align":
            text = re.sub(r"^\\begin\{align\}", "", text)
            text = re.sub(r"\\end\{align\}$", "", text)
            return text.strip()
        return text

    def _normalize_equations(self, expressions: list[ExtractedMathExpression]) -> list[Equation]:
        equations: list[Equation] = []
        for expr in expressions:
            body = self._strip_delimiters(expr.raw_latex, expr.environment_type)

            parts = [body]
            if expr.environment_type == "align":
                parts = [p.strip() for p in re.split(r"\\\\\s*", body) if p.strip()]

            for part in parts:
                clean = part.replace("&", "").strip()
                if "=" not in clean:
                    continue
                lhs, rhs = clean.split("=", 1)
                equations.append(
                    Equation(
                        raw=part.strip(),
                        lhs=lhs.strip(),
                        rhs=rhs.strip(),
                        source_location=f"line:{expr.line_number}:{expr.environment_type}",
                    )
                )
        return equations

    def extract(self, artifact_path: Path) -> list[ExtractedMathExpression]:
        text = artifact_path.read_text()
        block_expressions, consumed_spans = self._extract_blocks(text)
        inline_expressions = self._extract_inline(text, consumed_spans)
        expressions = block_expressions + inline_expressions
        expressions.sort(key=lambda item: item.line_number)
        return expressions

    def validate(self, artifact_path: Path) -> ValidationResult:
        """Extract math expressions and normalized equations from a .tex artifact."""
        path = Path(artifact_path)
        errors: list[str] = []

        if not path.exists():
            return ValidationResult(
                name=self.name,
                passed=False,
                errors=[f"Artifact not found: {path}"],
                metadata={"artifact_path": str(path), "expressions": [], "equations": []},
            )

        if path.suffix.lower() != ".tex":
            errors.append("Expected a .tex file")

        expressions = self.extract(path)
        equations = self._normalize_equations(expressions)

        return ValidationResult(
            name=self.name,
            passed=not errors,
            errors=errors,
            metadata={
                "artifact_path": str(path),
                "expression_count": len(expressions),
                "expressions": [asdict(expr) for expr in expressions],
                "equation_count": len(equations),
                "equations": [asdict(eq) for eq in equations],
            },
        )
