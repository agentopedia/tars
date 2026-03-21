from __future__ import annotations

import argparse
from pathlib import Path

from tars.validators.research.math.math_validator import MathValidator


def _cmd_validate_math(args: argparse.Namespace) -> int:
    validator = MathValidator()
    result = validator.validate(Path(args.paper))

    metrics = result.metadata.get("metrics", {})
    total = metrics.get("total_equations", result.metadata.get("equation_count", 0))
    validated = metrics.get("validated_equations", 0)
    failed = metrics.get("failed_equations", 0)
    skipped = metrics.get("skipped_equations", 0)

    print(f"Math validation: status={result.status or ('PASS' if result.passed else 'FAIL')}")
    if result.reason:
        print(f"Reason: {result.reason}")
    print(
        "Summary: "
        f"total_equations={total} "
        f"validated_equations={validated} "
        f"failed_equations={failed} "
        f"skipped_equations={skipped}"
    )

    if result.errors:
        print("Errors:")
        for err in result.errors:
            print(f"- {err}")

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="TARS command-line interface")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_math = subparsers.add_parser(
        "validate-math",
        help="Run math validation pipeline on a LaTeX paper (.tex)",
    )
    validate_math.add_argument("paper", help="Path to paper .tex file")
    validate_math.set_defaults(func=_cmd_validate_math)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
