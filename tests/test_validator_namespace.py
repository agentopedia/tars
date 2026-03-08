from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tars.validators import (
    BaseValidator,
    ValidationEngine,
    ValidationResult,
    ValidatorRegistry,
)


class DummyLatexValidator(BaseValidator):
    name = "latex"
    artifact_type = "latex"

    def validate(self, artifact_path: Path) -> ValidationResult:
        return ValidationResult(
            name=self.name,
            passed=artifact_path.suffix == ".tex",
            errors=[] if artifact_path.suffix == ".tex" else ["Expected .tex file"],
            metadata={"artifact_type": self.artifact_type, "path": str(artifact_path)},
        )


class DummyCitationValidator(BaseValidator):
    name = "citations"
    artifact_type = "bibliography"

    def validate(self, artifact_path: Path) -> ValidationResult:
        has_bib = artifact_path.with_suffix(".bib").exists()
        return ValidationResult(
            name=self.name,
            passed=has_bib,
            errors=[] if has_bib else ["Missing .bib file"],
            metadata={"artifact_type": self.artifact_type, "path": str(artifact_path)},
        )


class ValidatorNamespaceTests(unittest.TestCase):
    def test_validation_result_json_serializable(self):
        result = ValidationResult(
            name="latex",
            passed=False,
            errors=["Missing \\begin{document}", "Undefined citation: smith2024"],
            metadata={"phase": "mvp", "artifact": "paper.tex"},
        )

        payload = result.to_dict()
        encoded = json.dumps(payload)

        self.assertIn('"name": "latex"', encoded)
        self.assertIn('"passed": false', encoded)
        self.assertEqual(payload["errors"][0], "Missing \\begin{document}")

    def test_registry_plugin_architecture(self):
        registry = ValidatorRegistry()
        validator = DummyLatexValidator()
        registry.register(validator)

        self.assertEqual(registry.list_names(), ["latex"])

        ok = registry.validate_with("latex", Path("paper.tex"))
        bad = registry.validate_with("latex", Path("paper.md"))

        self.assertTrue(ok.passed)
        self.assertFalse(bad.passed)
        self.assertEqual(bad.errors, ["Expected .tex file"])

    def test_engine_orchestrates_multiple_validators(self):
        engine = ValidationEngine()
        engine.register_validators([DummyLatexValidator(), DummyCitationValidator()])

        with self.subTest("all validators run"):
            results = engine.run(Path("paper.tex"))
            self.assertEqual(len(results), 2)
            self.assertEqual({r.name for r in results}, {"latex", "citations"})

        with self.subTest("aggregates"):
            summary = engine.aggregate(results)
            self.assertEqual(summary["total"], 2)
            self.assertEqual(summary["failed"], 1)
            self.assertFalse(summary["all_passed"])


if __name__ == "__main__":
    unittest.main()
