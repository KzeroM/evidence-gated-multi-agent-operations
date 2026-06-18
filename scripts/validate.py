#!/usr/bin/env python3
"""Repository validation for the reference package.

Checks that the example YAML blocks satisfy the schemas and that public text does
not contain obvious private-operation tokens. The script intentionally uses only
small, inspectable rules so the reference package remains vendor-neutral.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"

MISSION_SCHEMA = json.loads((SCHEMAS / "mission-contract.schema.json").read_text())
FINAL_REPORT_SCHEMA = json.loads((SCHEMAS / "final-report.schema.json").read_text())

PRIVATE_PATTERNS = [
    r"Z-[A-Za-z]+",
    r"Z\.R\.I\.D\.A\.Y",
    r"Z\.A\.R\.V\.I\.S\.",
    r"@vps_agent",
    r"@local_agent",
    r"Zeroson",
    r"telegram:[0-9-]+",
    r"127\.0\.0\.1:[0-9]{2,5}",
    r"(?i)(api[_-]?key|secret|token|cookie)\s*[:=]\s*['\"]?[A-Za-z0-9_\-.]{8,}",
]
ALLOW_PRIVATE_PATTERN_FILES = {"examples/sanitization-search.txt", "scripts/validate.py"}


def iter_markdown_files() -> list[Path]:
    return sorted(p for p in ROOT.rglob("*.md") if ".git" not in p.parts and "node_modules" not in p.parts)


def fenced_yaml_blocks(path: Path):
    text = path.read_text()
    for match in re.finditer(r"```ya?ml\n(.*?)\n```", text, re.DOTALL):
        yield match.start(), match.group(1)


def validate_instance(instance, schema, label: str) -> list[str]:
    validator = Draft202012Validator(schema)
    errors = []
    for error in sorted(validator.iter_errors(instance), key=lambda e: list(e.path)):
        path = "/".join(str(p) for p in error.absolute_path) or "<root>"
        errors.append(f"{label}: {path}: {error.message}")
    return errors


def _contains_placeholder(value) -> bool:
    if isinstance(value, str):
        return "|" in value or value.startswith("What ") or value.startswith("How ")
    if isinstance(value, dict):
        return any(_contains_placeholder(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_placeholder(item) for item in value)
    return False


def _is_template_placeholder(instance: dict) -> bool:
    return _contains_placeholder(instance)


def validate_yaml_examples() -> list[str]:
    errors: list[str] = []
    for path in iter_markdown_files():
        rel = path.relative_to(ROOT)
        for pos, block in fenced_yaml_blocks(path):
            try:
                parsed = yaml.safe_load(block)
            except Exception as exc:  # pragma: no cover - diagnostic path
                errors.append(f"{rel}:{pos}: invalid YAML: {exc}")
                continue
            if isinstance(parsed, dict) and "mission" in parsed:
                if _is_template_placeholder(parsed):
                    continue
                errors.extend(validate_instance(parsed, MISSION_SCHEMA, f"{rel}:{pos}: mission contract"))
            elif isinstance(parsed, dict) and "summary" in parsed and "verified" in parsed:
                errors.extend(validate_instance(parsed, FINAL_REPORT_SCHEMA, f"{rel}:{pos}: final report"))
    return errors


def validate_schema_files() -> list[str]:
    errors: list[str] = []
    for schema_path in sorted(SCHEMAS.glob("*.schema.json")):
        try:
            schema = json.loads(schema_path.read_text())
            Draft202012Validator.check_schema(schema)
        except Exception as exc:
            errors.append(f"{schema_path.relative_to(ROOT)}: invalid JSON Schema: {exc}")
    return errors


def validate_local_markdown_links() -> list[str]:
    errors: list[str] = []
    link_re = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for path in iter_markdown_files():
        rel = path.relative_to(ROOT)
        text = path.read_text()
        for match in link_re.finditer(text):
            target = match.group(1).strip()
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = target.split("#", 1)[0]
            if not target:
                continue
            resolved = (path.parent / target).resolve()
            try:
                resolved.relative_to(ROOT)
            except ValueError:
                errors.append(f"{rel}: link escapes repository: {match.group(1)}")
                continue
            if not resolved.exists():
                line = text.count("\n", 0, match.start()) + 1
                errors.append(f"{rel}:{line}: broken local link: {match.group(1)}")
    return errors


def sanitization_scan() -> list[str]:
    errors: list[str] = []
    files = [p for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts and "node_modules" not in p.parts]
    for path in files:
        rel = str(path.relative_to(ROOT))
        if rel in ALLOW_PRIVATE_PATTERN_FILES:
            continue
        if path.suffix not in {".md", ".txt", ".json", ".yml", ".yaml", ".mmd", ".py"}:
            continue
        text = path.read_text(errors="ignore")
        for pattern in PRIVATE_PATTERNS:
            for match in re.finditer(pattern, text):
                line = text.count("\n", 0, match.start()) + 1
                errors.append(f"{rel}:{line}: sanitization pattern matched: {pattern}")
    return errors


def main() -> int:
    errors = []
    errors.extend(validate_schema_files())
    errors.extend(validate_yaml_examples())
    errors.extend(validate_local_markdown_links())
    errors.extend(sanitization_scan())

    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Validation passed: schemas, YAML examples, local links, and sanitization scan are OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
