#!/usr/bin/env python3
"""Validate self-improvement gallery artifacts against the shared schema."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

try:
    from jsonschema import Draft7Validator, ValidationError
except ImportError as exc:  # pragma: no cover - defensive guard
    raise SystemExit("jsonschema is required: pip install jsonschema") from exc


@dataclass
class ValidationIssue:
    path: Path
    message: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Repository root (defaults to current working directory)",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path("docs/case-studies/gallery.schema.json"),
        help="Path to gallery JSON schema",
    )
    parser.add_argument(
        "--artifacts",
        type=Path,
        default=Path("docs/case-studies/artifacts"),
        help="Directory with plan JSON files",
    )
    return parser.parse_args()


def load_schema(schema_path: Path) -> Draft7Validator:
    try:
        with schema_path.open("r", encoding="utf-8") as stream:
            schema = json.load(stream)
    except FileNotFoundError:
        raise SystemExit(f"Schema not found: {schema_path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid schema JSON at {schema_path}: {exc}")
    return Draft7Validator(schema)


def validate_plan(
    plan_path: Path, validator: Draft7Validator, repo_root: Path
) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    try:
        with plan_path.open("r", encoding="utf-8") as stream:
            data = json.load(stream)
    except json.JSONDecodeError as exc:
        issues.append(ValidationIssue(plan_path, f"Invalid JSON: {exc}"))
        return issues

    for error in validator.iter_errors(data):
        location = " / ".join(str(elem) for elem in error.path) or "root"
        issues.append(ValidationIssue(plan_path, f"Schema error at {location}: {error.message}"))

    artifacts: Dict[str, str] = data.get("artifacts", {})
    for label, rel_path in artifacts.items():
        ref_path = (repo_root / rel_path).resolve()
        if not ref_path.exists():
            issues.append(ValidationIssue(plan_path, f"Missing artifact '{label}': {ref_path}"))

    return issues


def main() -> int:
    args = parse_args()
    repo_root = args.root.resolve()
    schema_path = (repo_root / args.schema).resolve()
    artifacts_dir = (repo_root / args.artifacts).resolve()

    if not artifacts_dir.exists():
        raise SystemExit(f"Artifacts directory not found: {artifacts_dir}")

    validator = load_schema(schema_path)

    plan_files = sorted(artifacts_dir.glob("*-plan.json"))
    if not plan_files:
        print(f"No plan files found in {artifacts_dir}")
        return 0

    issues: List[ValidationIssue] = []
    for plan_path in plan_files:
        issues.extend(validate_plan(plan_path, validator, repo_root))

    if issues:
        print("Validation failed:")
        for issue in issues:
            print(f" - {issue.path.relative_to(repo_root)} :: {issue.message}")
        return 1

    print(f"Validated {len(plan_files)} plan file(s) with no issues.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
