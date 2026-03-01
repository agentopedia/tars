from __future__ import annotations

from pathlib import Path

from tars.validators.base import BaseValidator
from tars.validators.result import ValidationResult


class MathExtractor(BaseValidator):
    """Extract mathematical expressions from research artifacts.

    This validator skeleton will eventually identify and normalize equations,
    inline formulas, and math blocks from a paper input for downstream checks.
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

            # Skip escaped dollar
            if i > 0 and text[i - 1] == "\\":
                i += 1
                continue

            # Skip $$ blocks (not requested for this FR)
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

    def extract(self, artifact_path: Path) -> list[ExtractedMathExpression]:
        text = artifact_path.read_text()
        block_expressions, consumed_spans = self._extract_blocks(text)
        inline_expressions = self._extract_inline(text, consumed_spans)
        expressions = block_expressions + inline_expressions
        expressions.sort(key=lambda item: item.line_number)
        return expressions

    def validate(self, artifact_path: Path) -> ValidationResult:
        """Extract all supported math expressions and return standardized output."""
        path = Path(artifact_path)
        errors: list[str] = []

        if not path.exists():
            return ValidationResult(
                name=self.name,
                passed=False,
                errors=[f"Artifact not found: {path}"],
                metadata={"artifact_path": str(path), "expressions": []},
            )

        if path.suffix.lower() != ".tex":
            errors.append("Expected a .tex file")

        expressions = self.extract(path)
        return ValidationResult(
            name=self.name,
            passed=not errors,
            errors=errors,
            metadata={
                "artifact_path": str(path),
                "expression_count": len(expressions),
                "expressions": [asdict(expr) for expr in expressions],
            },
        )
