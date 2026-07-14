"""Command-line interface for protocol validation, judgment, and task creation."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml

from .protocol import (
    ROOT,
    load_documents,
    sanitization_scan,
    validate_chain,
    validate_local_links,
    validate_repository_documents,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="egmo", description="EGMO v2 protocol utilities")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate", help="validate protocol documents and repository safety")
    validate.add_argument("paths", nargs="*", type=Path)
    validate.add_argument("--mode", choices=["working-tree", "tracked", "history"], default="working-tree")
    validate.add_argument("--no-sanitization", action="store_true")
    judge = sub.add_parser("judge", help="judge a mission-to-report document chain")
    judge.add_argument("paths", nargs="+", type=Path)
    judge.add_argument("--as-of", help="RFC3339 freshness time; defaults to review time")
    create = sub.add_parser("create-task", help="copy a v2 task packet without executing it")
    create.add_argument("output", type=Path)
    create.add_argument("--mission-id", required=True)
    return parser


def _print_errors(errors: list[str]) -> int:
    if errors:
        print("Validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    return 0


def _validate(args: argparse.Namespace) -> int:
    if args.paths:
        paths = [path.resolve() for path in args.paths]
        documents, errors = load_documents(paths)
        errors.extend(validate_chain(documents))
    else:
        documents, errors = validate_repository_documents()
        errors.extend(validate_local_links())
    if not args.no_sanitization:
        errors.extend(sanitization_scan(args.mode))
    code = _print_errors(errors)
    if code == 0:
        checks = "documents"
        if not args.paths:
            checks += ", local links"
        if not args.no_sanitization:
            checks += f", and {args.mode} sanitization"
        print(f"Validated {len(documents)} EGMO v2 document(s); {checks} passed.")
    return code


def _judge(args: argparse.Namespace) -> int:
    documents, errors = load_documents([path.resolve() for path in args.paths])
    as_of = datetime.fromisoformat(args.as_of.replace("Z", "+00:00")) if args.as_of else None
    errors.extend(validate_chain(documents, as_of=as_of))
    kinds = {doc.data.get("document_type") for doc in documents}
    required = {"mission_contract", "execution_record", "evidence_record", "critic_review", "final_report"}
    missing = required - kinds
    if missing:
        errors.append(f"judge requires a complete chain; missing {sorted(missing)}")
    for kind in required:
        count = sum(doc.data.get("document_type") == kind for doc in documents)
        if count > 1:
            errors.append(f"judge requires exactly one {kind}; found {count}")
    code = _print_errors(errors)
    if code:
        return code
    report = next(doc.data for doc in documents if doc.data["document_type"] == "final_report")
    review = next(doc.data for doc in documents if doc.data["document_type"] == "critic_review")
    if report["judgment"] == "PASSED" and review["verdict"] == "PASS":
        print(f"PASSED: {report['mission_id']} subject {report['subject']['value']}")
        return 0
    print(f"NOT_PASSED: judgment={report['judgment']} verdict={review['verdict']}")
    return 1


def _create_task(args: argparse.Namespace) -> int:
    if not re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", args.mission_id) or not 3 <= len(args.mission_id) <= 60:
        print("mission ID must be a 3-60 character lowercase hyphenated protocol ID", file=sys.stderr)
        return 2
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        print(f"output directory is not empty: {output}", file=sys.stderr)
        return 2
    output.mkdir(parents=True, exist_ok=True)
    mapping = {
        "mission.yaml": "mission.yaml",
        "execution.yaml": "execution-record.yaml",
        "evidence.yaml": "evidence.yaml",
        "review.yaml": "critic-review.yaml",
        "final-report.yaml": "final-report.yaml",
    }
    replacements = {
        "example-mission-0001": args.mission_id,
        "example-approval-0001": f"{args.mission_id}-approval",
        "example-execution-0001": f"{args.mission_id}-execution",
        "example-worker-run-0001": f"{args.mission_id}-worker-run",
        "example-evidence-record-0001": f"{args.mission_id}-evidence-record",
        "example-artifact-evidence-0001": f"{args.mission_id}-artifact-evidence",
        "example-command-evidence-0001": f"{args.mission_id}-command-evidence",
        "example-review-0001": f"{args.mission_id}-review",
        "example-review-run-0001": f"{args.mission_id}-review-run",
        "example-report-0001": f"{args.mission_id}-report",
    }

    def replace_ids(value: object) -> object:
        if isinstance(value, str):
            for old, new in replacements.items():
                value = value.replace(old, new)
            return value
        if isinstance(value, list):
            return [replace_ids(item) for item in value]
        if isinstance(value, dict):
            return {key: replace_ids(item) for key, item in value.items()}
        return value

    for destination, source in mapping.items():
        data = yaml.safe_load((ROOT / "templates" / source).read_text(encoding="utf-8"))
        data = replace_ids(data)
        (output / destination).write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    print(f"Created protocol packet at {output}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "validate":
            return _validate(args)
        if args.command == "judge":
            return _judge(args)
        return _create_task(args)
    except (OSError, ValueError, yaml.YAMLError, subprocess.SubprocessError) as exc:
        print(f"egmo: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
