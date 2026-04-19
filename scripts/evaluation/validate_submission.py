"""
Validate a DeepSynth leaderboard submission file against the submission schema
and against benchmark-specific semantic checks.

Usage:
    python validate_submission.py path/to/submission.json
    python validate_submission.py path/to/submission.json --strict

Exit codes:
    0 - submission valid
    1 - schema violation
    2 - semantic violation (missing task IDs, unknown task IDs, etc.)
    3 - file/IO error
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import jsonschema
    from jsonschema import Draft202012Validator
except ImportError:
    print("ERROR: jsonschema is required. Install with: pip install jsonschema", file=sys.stderr)
    sys.exit(3)


# Resolve paths relative to this file so the validator works from any cwd.
HERE = Path(__file__).resolve().parent
SCHEMA_PATH = HERE / "submission_schema.json"

# Expected test-set task IDs. Populate from the actual benchmark on release.
# These are placeholders — wire this to load from the HF dataset in production.
EXPECTED_TEST_IDS: set[str] = {f"{i:03d}" for i in range(1, 121)}  # 001..120
EXPECTED_DEV_IDS: set[str] = {f"{i:03d}" for i in range(1, 41)}    # 001..040


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_schema() -> dict:
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema not found at {SCHEMA_PATH}")
    return load_json(SCHEMA_PATH)


def validate_schema(submission: dict, schema: dict) -> list[str]:
    """Return a list of schema error messages (empty if valid)."""
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(submission), key=lambda e: list(e.absolute_path))
    return [
        f"[schema] {'/'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}"
        for e in errors
    ]


def validate_semantics(submission: dict, strict: bool = False) -> list[str]:
    """Benchmark-specific checks that JSON Schema can't express."""
    errors: list[str] = []

    split = submission.get("metadata", {}).get("split")
    predictions = submission.get("predictions", {})
    submitted_ids = set(predictions.keys())

    if split == "dev":
        expected = EXPECTED_DEV_IDS
    elif split in ("test", "full"):
        expected = EXPECTED_TEST_IDS
    else:
        return errors  # schema validator will have caught missing split

    unknown = submitted_ids - expected
    if unknown:
        errors.append(
            f"[semantic] {len(unknown)} unknown task ID(s) for split={split}: "
            f"{sorted(unknown)[:5]}{'...' if len(unknown) > 5 else ''}"
        )

    missing = expected - submitted_ids
    if missing:
        msg = (
            f"[semantic] Missing predictions for {len(missing)} task(s) in split={split}: "
            f"{sorted(missing)[:5]}{'...' if len(missing) > 5 else ''}"
        )
        if strict:
            errors.append(msg)
        else:
            print(f"WARNING: {msg}", file=sys.stderr)

    # Flag submissions that claim to use external retrieval but list no tools.
    meta = submission.get("metadata", {})
    if meta.get("uses_external_retrieval") and not meta.get("tools_used"):
        errors.append(
            "[semantic] uses_external_retrieval=true but tools_used is empty. "
            "Declare the tools your agent used."
        )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a DeepSynth submission file.")
    parser.add_argument("submission", type=Path, help="Path to submission JSON file.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat missing task IDs as errors rather than warnings.",
    )
    args = parser.parse_args()

    if not args.submission.exists():
        print(f"ERROR: file not found: {args.submission}", file=sys.stderr)
        return 3

    try:
        submission = load_json(args.submission)
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid JSON: {e}", file=sys.stderr)
        return 3

    try:
        schema = load_schema()
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"ERROR: failed to load schema: {e}", file=sys.stderr)
        return 3

    schema_errors = validate_schema(submission, schema)
    if schema_errors:
        print("Schema validation FAILED:", file=sys.stderr)
        for err in schema_errors:
            print(f"  {err}", file=sys.stderr)
        return 1

    semantic_errors = validate_semantics(submission, strict=args.strict)
    if semantic_errors:
        print("Semantic validation FAILED:", file=sys.stderr)
        for err in semantic_errors:
            print(f"  {err}", file=sys.stderr)
        return 2

    meta = submission["metadata"]
    n_preds = len(submission["predictions"])
    print(
        f"OK: submission valid. "
        f"agent={meta['agent_name']} | model={meta['base_model']} | "
        f"scaffold={meta['scaffold']} | split={meta['split']} | "
        f"predictions={n_preds}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
