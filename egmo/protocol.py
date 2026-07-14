"""Schema and cross-document validation for the EGMO v2 protocol."""

from __future__ import annotations

import ipaddress
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

SOURCE_ROOT = Path(__file__).resolve().parents[1]
ROOT = SOURCE_ROOT if (SOURCE_ROOT / "pyproject.toml").is_file() else Path.cwd().resolve()
DATA_ROOT = (
    SOURCE_ROOT
    if (SOURCE_ROOT / "schemas").is_dir()
    else Path(sys.prefix) / "share" / "egmo"
)
SCHEMA_DIR = DATA_ROOT / "schemas"
TEMPLATE_DIR = DATA_ROOT / "templates"
POLICY_PATH = (
    ROOT / "sanitization-policy.yaml"
    if (ROOT / "sanitization-policy.yaml").is_file()
    else DATA_ROOT / "sanitization-policy.yaml"
)

SCHEMA_FILES = {
    "mission_contract": "mission-contract.schema.json",
    "execution_record": "execution-record.schema.json",
    "evidence_record": "evidence.schema.json",
    "critic_review": "critic-review.schema.json",
    "final_report": "final-report.schema.json",
}

VERDICT_TO_JUDGMENT = {
    "PASS": "PASSED",
    "REQUEST_CHANGES": "CHANGES_REQUESTED",
    "BLOCKED": "BLOCKED",
    "INCONCLUSIVE": "INCONCLUSIVE",
}

JUDGMENT_STATES = {
    "PASSED": {"PASSED"},
    "CHANGES_REQUESTED": {"CHANGES_REQUESTED"},
    "BLOCKED": {"BLOCKED"},
    "INCONCLUSIVE": {"EVIDENCE_PENDING", "REVIEW_PENDING"},
    "PARTIAL_SUCCESS": {"PARTIAL_SUCCESS"},
    "CANCELLED": {"CANCELLED"},
    "ROLLED_BACK": {"ROLLED_BACK"},
}

ALLOWED_STATE_TRANSITIONS = {
    "DRAFT": {"APPROVAL_PENDING", "APPROVED", "CANCELLED"},
    "APPROVAL_PENDING": {"APPROVED", "BLOCKED", "CANCELLED"},
    "APPROVED": {"RUNNING", "CANCELLED"},
    "RUNNING": {
        "EVIDENCE_PENDING", "REVIEW_PENDING", "PARTIAL_SUCCESS", "BLOCKED",
        "CHANGES_REQUESTED", "CANCELLED", "ROLLBACK_PENDING",
    },
    "EVIDENCE_PENDING": {
        "REVIEW_PENDING", "RUNNING", "BLOCKED", "CHANGES_REQUESTED", "CANCELLED",
        "ROLLBACK_PENDING",
    },
    "REVIEW_PENDING": {
        "PASSED", "CHANGES_REQUESTED", "BLOCKED", "EVIDENCE_PENDING", "CANCELLED",
        "PARTIAL_SUCCESS", "ROLLBACK_PENDING",
    },
    "CHANGES_REQUESTED": {"RUNNING", "CANCELLED", "ROLLBACK_PENDING"},
    "BLOCKED": {"RUNNING", "CANCELLED", "ROLLBACK_PENDING"},
    "PARTIAL_SUCCESS": {"REVIEW_PENDING", "ROLLBACK_PENDING", "CHANGES_REQUESTED", "BLOCKED"},
    "ROLLBACK_PENDING": {"ROLLED_BACK", "BLOCKED"},
    "PASSED": set(),
    "CANCELLED": set(),
    "ROLLED_BACK": set(),
}

FORMAT_CHECKER = FormatChecker()


@FORMAT_CHECKER.checks("date-time", raises=(TypeError, ValueError))
def _valid_date_time(value: str) -> bool:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.tzinfo is not None


@FORMAT_CHECKER.checks("uri", raises=(TypeError, ValueError))
def _valid_uri(value: str) -> bool:
    return bool(urlparse(value).scheme)


@dataclass(frozen=True)
class LoadedDocument:
    data: dict[str, Any]
    label: str


def _schema_registry() -> tuple[dict[str, dict[str, Any]], Registry]:
    schemas: dict[str, dict[str, Any]] = {}
    resources: list[tuple[str, Resource[dict[str, Any]]]] = []
    for path in sorted(SCHEMA_DIR.glob("*.schema.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        schemas[path.name] = schema
        resources.append((schema["$id"], Resource.from_contents(schema)))
    return schemas, Registry().with_resources(resources)


def validate_document(document: dict[str, Any], label: str = "document") -> list[str]:
    kind = document.get("document_type")
    version = document.get("schema_version")
    if not kind or not version:
        return [f"{label}: fenced/machine-checkable YAML must declare document_type and schema_version"]
    if version != "2.0":
        return [f"{label}: unsupported schema_version {version!r}; expected '2.0'"]
    filename = SCHEMA_FILES.get(kind)
    if filename is None:
        return [f"{label}: unsupported document_type {kind!r}"]
    schemas, registry = _schema_registry()
    validator = Draft202012Validator(
        schemas[filename], registry=registry, format_checker=FORMAT_CHECKER
    )
    errors: list[str] = []
    for error in sorted(validator.iter_errors(document), key=lambda item: list(item.absolute_path)):
        path = "/".join(str(part) for part in error.absolute_path) or "<root>"
        errors.append(f"{label}: {path}: {error.message}")
    errors.extend(_validate_formats(document, label))
    errors.extend(_validate_subject_kinds(document, label))
    return errors


def _validate_formats(value: Any, label: str, path: tuple[str, ...] = ()) -> list[str]:
    """Enforce core formats even with distro jsonschema builds lacking extras."""
    errors: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            item_path = (*path, key)
            if key in {"created_at", "approved_at", "expires_at", "captured_at", "started_at", "ended_at", "reviewed_at", "valid_until", "at", "requested_at"} and isinstance(item, str):
                try:
                    _valid_date_time(item)
                except (TypeError, ValueError):
                    errors.append(f"{label}: {'/'.join(item_path)}: {item!r} is not a date-time")
            if key in {"uri", "source_uri"} and isinstance(item, str) and not _valid_uri(item):
                errors.append(f"{label}: {'/'.join(item_path)}: {item!r} is not an absolute URI")
            errors.extend(_validate_formats(item, label, item_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            errors.extend(_validate_formats(item, label, (*path, str(index))))
    return errors


def _validate_subject_kinds(value: Any, label: str, path: tuple[str, ...] = ()) -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        if {"kind", "algorithm", "value"}.issubset(value) and value.get("kind") in {
            "git_commit", "file", "oci_image", "deployment", "resource_revision"
        }:
            allowed = {
                "git_commit": {"git-sha1"},
                "file": {"sha256"},
                "oci_image": {"sha256"},
                "deployment": {"sha256", "version"},
                "resource_revision": {"sha256", "version"},
            }
            if value["algorithm"] not in allowed[value["kind"]]:
                errors.append(
                    f"{label}: {'/'.join(path) or '<root>'}: algorithm {value['algorithm']} "
                    f"is not valid for subject kind {value['kind']}"
                )
        for key, item in value.items():
            errors.extend(_validate_subject_kinds(item, label, (*path, key)))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            errors.extend(_validate_subject_kinds(item, label, (*path, str(index))))
    return errors


def fenced_yaml_blocks(path: Path) -> Iterable[tuple[int, str]]:
    text = path.read_text(encoding="utf-8")
    for match in re.finditer(r"^```ya?ml[^\n]*\n(.*?)^```", text, re.DOTALL | re.MULTILINE):
        yield text.count("\n", 0, match.start()) + 1, match.group(1)


def load_documents(paths: Iterable[Path]) -> tuple[list[LoadedDocument], list[str]]:
    documents: list[LoadedDocument] = []
    errors: list[str] = []
    for path in sorted(set(paths)):
        rel = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
        if path.suffix.lower() in {".yaml", ".yml"}:
            candidates = [(1, path.read_text(encoding="utf-8"))]
        elif path.suffix.lower() == ".md":
            candidates = list(fenced_yaml_blocks(path))
        else:
            continue
        for line, source in candidates:
            label = f"{rel}:{line}"
            try:
                parsed = yaml.safe_load(source)
            except yaml.YAMLError as exc:
                errors.append(f"{label}: invalid YAML: {exc}")
                continue
            if not isinstance(parsed, dict):
                errors.append(f"{label}: machine-checkable YAML must be an object")
                continue
            document_errors = validate_document(parsed, label)
            errors.extend(document_errors)
            if not document_errors:
                documents.append(LoadedDocument(parsed, label))
    return documents, errors


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _subject_key(subject: dict[str, Any] | None) -> tuple[Any, ...] | None:
    if not subject:
        return None
    return subject.get("kind"), subject.get("algorithm"), subject.get("value")


def validate_document_semantics(document: LoadedDocument) -> list[str]:
    data, label = document.data, document.label
    errors: list[str] = []
    kind = data.get("document_type")
    if kind == "mission_contract":
        criterion_ids = [item["criterion_id"] for item in data.get("success_criteria", [])]
        if len(criterion_ids) != len(set(criterion_ids)):
            errors.append(f"{label}: criterion_id values must be unique")
        approval = data.get("approval", {})
        risk = data.get("risk", {})
        if risk.get("production") and risk.get("level") != "high":
            errors.append(f"{label}: production work must use risk.level high")
        if risk.get("level") in {"medium", "high"} and approval.get("kind") != "explicit":
            errors.append(f"{label}: medium/high risk requires explicit approval")
        if "expires_at" in approval and _parse_time(approval["expires_at"]) <= _parse_time(approval["approved_at"]):
            errors.append(f"{label}: approval expires_at must be after approved_at")
    elif kind == "execution_record":
        history = data.get("state_history", [])
        if history and history[0].get("state") != "DRAFT":
            errors.append(f"{label}: state_history must begin with DRAFT")
        if history and history[-1].get("state") != data.get("current_state"):
            errors.append(f"{label}: current_state must equal the final state_history entry")
        if data.get("attempt", 0) > data.get("retry_policy", {}).get("max_attempts", 0):
            errors.append(f"{label}: attempt exceeds retry_policy.max_attempts")
        expected_remaining = data.get("retry_policy", {}).get("max_attempts", 0) - data.get("attempt", 0)
        if data.get("retry_policy", {}).get("remaining_attempts") != expected_remaining:
            errors.append(f"{label}: retry_policy.remaining_attempts must equal max_attempts - attempt")
        timestamps = [_parse_time(item["at"]) for item in history]
        if timestamps != sorted(timestamps):
            errors.append(f"{label}: state_history timestamps must be ordered")
        for previous, current in zip(history, history[1:]):
            if current["state"] not in ALLOWED_STATE_TRANSITIONS[previous["state"]]:
                errors.append(
                    f"{label}: invalid state transition {previous['state']} -> {current['state']}"
                )
        state = data.get("current_state")
        cancellation = data.get("cancellation")
        rollback = data.get("rollback_or_compensation")
        if state == "CANCELLED" and cancellation is None:
            errors.append(f"{label}: CANCELLED requires cancellation metadata")
        if state in {"ROLLBACK_PENDING", "ROLLED_BACK"} and rollback is None:
            errors.append(f"{label}: {state} requires rollback_or_compensation metadata")
        if state == "ROLLBACK_PENDING" and rollback and rollback.get("status") != "pending":
            errors.append(f"{label}: ROLLBACK_PENDING requires rollback status pending")
        if state == "ROLLED_BACK" and rollback and rollback.get("status") != "completed":
            errors.append(f"{label}: ROLLED_BACK requires rollback status completed")
    elif kind == "evidence_record":
        seen: set[str] = set()
        for item in data.get("items", []):
            if item["evidence_id"] in seen:
                errors.append(f"{label}: duplicate evidence_id {item['evidence_id']}")
            seen.add(item["evidence_id"])
            if _parse_time(item["expires_at"]) <= _parse_time(item["captured_at"]):
                errors.append(f"{label}: {item['evidence_id']} expires_at must follow captured_at")
            if _subject_key(item.get("subject")) != _subject_key(data.get("subject")):
                errors.append(f"{label}: {item['evidence_id']} subject differs from record subject")
            details = item.get("details", {})
            evidence_type = item.get("evidence_type")
            is_command = {
                "command", "exit_status", "started_at", "ended_at", "environment_ref", "output_artifact"
            }.issubset(details)
            is_api = {"source_uri", "artifact"}.issubset(details)
            is_artifact = {"artifact", "media_type"}.issubset(details)
            if evidence_type in {"command_result", "test_result"} and not is_command:
                errors.append(f"{label}: {item['evidence_id']} requires command result details")
            if evidence_type == "api_response" and not is_api:
                errors.append(f"{label}: {item['evidence_id']} requires API response details")
            if evidence_type in {"read_back", "artifact"} and not is_artifact:
                errors.append(f"{label}: {item['evidence_id']} requires artifact/read-back details")
            if is_command and _parse_time(details["ended_at"]) < _parse_time(details["started_at"]):
                errors.append(f"{label}: {item['evidence_id']} command ended before it started")
            if is_command and _parse_time(item["captured_at"]) < _parse_time(details["ended_at"]):
                errors.append(f"{label}: {item['evidence_id']} was captured before the command ended")
    elif kind == "critic_review":
        statuses = [item["status"] for item in data.get("criteria", [])]
        verdict = data.get("verdict")
        if verdict == "PASS" and any(status != "satisfied" for status in statuses):
            errors.append(f"{label}: PASS requires every criterion to be satisfied")
        if verdict == "PASS" and data.get("must_fix"):
            errors.append(f"{label}: PASS cannot contain must_fix items")
        if verdict == "REQUEST_CHANGES" and not data.get("must_fix"):
            errors.append(f"{label}: REQUEST_CHANGES requires at least one must_fix item")
        if verdict == "REQUEST_CHANGES" and "not_satisfied" not in statuses:
            errors.append(f"{label}: REQUEST_CHANGES requires a not_satisfied criterion")
        if verdict == "BLOCKED" and (not data.get("findings") or all(status == "satisfied" for status in statuses)):
            errors.append(f"{label}: BLOCKED requires a blocking finding and an unresolved criterion")
        if verdict == "INCONCLUSIVE" and "insufficient_evidence" not in statuses:
            errors.append(f"{label}: INCONCLUSIVE requires an insufficient_evidence criterion")
        if _parse_time(data["valid_until"]) <= _parse_time(data["reviewed_at"]):
            errors.append(f"{label}: valid_until must follow reviewed_at")
        for deferral in data.get("deferrals", []):
            expires = _parse_time(deferral["expires_at"])
            if expires <= _parse_time(data["reviewed_at"]):
                errors.append(f"{label}: deferral expires_at must follow reviewed_at")
            if expires > _parse_time(data["valid_until"]):
                errors.append(f"{label}: deferral cannot outlive review valid_until")
    return errors


def validate_chain(documents: Iterable[LoadedDocument], as_of: datetime | None = None) -> list[str]:
    docs = list(documents)
    errors: list[str] = []
    for doc in docs:
        errors.extend(validate_document_semantics(doc))
    by_kind: dict[str, list[LoadedDocument]] = {}
    for doc in docs:
        by_kind.setdefault(doc.data.get("document_type", ""), []).append(doc)
    if not all(kind in by_kind for kind in SCHEMA_FILES):
        return errors
    for kind, id_field in {
        "mission_contract": "mission_id",
        "execution_record": "execution_id",
        "evidence_record": "evidence_record_id",
        "critic_review": "review_id",
        "final_report": "report_id",
    }.items():
        values = [doc.data[id_field] for doc in by_kind[kind]]
        if len(values) != len(set(values)):
            errors.append(f"duplicate {id_field} values are not allowed")
    missions = {d.data["mission_id"]: d for d in by_kind["mission_contract"]}
    executions = {d.data["execution_id"]: d for d in by_kind["execution_record"]}
    evidence_records = {d.data["evidence_record_id"]: d for d in by_kind["evidence_record"]}
    reviews = {d.data["review_id"]: d for d in by_kind["critic_review"]}
    criterion_ids = {mid: {c["criterion_id"] for c in doc.data["success_criteria"]} for mid, doc in missions.items()}
    evidence_items: dict[str, tuple[LoadedDocument, dict[str, Any]]] = {}
    for record in evidence_records.values():
        for item in record.data["items"]:
            if item["evidence_id"] in evidence_items:
                errors.append(f"{record.label}: evidence_id {item['evidence_id']} is not globally unique")
            evidence_items[item["evidence_id"]] = (record, item)
    for execution in executions.values():
        mission = missions.get(execution.data["mission_id"])
        if mission is None:
            errors.append(f"{execution.label}: unknown mission_id")
        elif _subject_key(execution.data["input_subject"]) != _subject_key(mission.data["target_subject"]):
            errors.append(f"{execution.label}: input_subject does not match mission target_subject")
        elif execution.data.get("state_history"):
            running = next((item for item in execution.data["state_history"] if item["state"] == "RUNNING"), None)
            if running and _parse_time(running["at"]) < _parse_time(mission.data["approval"]["approved_at"]):
                errors.append(f"{execution.label}: execution started before approval")
            expires = mission.data["approval"].get("expires_at")
            if running and expires and _parse_time(running["at"]) > _parse_time(expires):
                errors.append(f"{execution.label}: execution started after approval expiry")
    for record in evidence_records.values():
        mission = missions.get(record.data["mission_id"])
        execution = executions.get(record.data["execution_id"])
        if mission is None or execution is None:
            errors.append(f"{record.label}: evidence references an unknown mission or execution")
            continue
        if execution.data["mission_id"] != record.data["mission_id"]:
            errors.append(f"{record.label}: evidence mission_id differs from its execution mission_id")
        expected_subject = execution.data.get("output_subject", execution.data["input_subject"])
        if _subject_key(record.data["subject"]) != _subject_key(expected_subject):
            errors.append(f"{record.label}: evidence subject does not match execution output subject")
        running_times = [
            _parse_time(item["at"])
            for item in execution.data["state_history"]
            if item["state"] == "RUNNING"
        ]
        for item in record.data["items"]:
            unknown = set(item["criterion_ids"]) - criterion_ids[mission.data["mission_id"]]
            if unknown:
                errors.append(f"{record.label}: {item['evidence_id']} references unknown criteria {sorted(unknown)}")
            if running_times and _parse_time(item["captured_at"]) < min(running_times):
                errors.append(f"{record.label}: {item['evidence_id']} was captured before execution started")
    for review in reviews.values():
        data = review.data
        mission = missions.get(data["mission_id"])
        execution = executions.get(data["execution_id"])
        if mission is None or execution is None:
            errors.append(f"{review.label}: review references an unknown mission or execution")
            continue
        if execution.data["mission_id"] != data["mission_id"]:
            errors.append(f"{review.label}: review mission_id differs from its execution mission_id")
        expected_subject = execution.data.get("output_subject", execution.data["input_subject"])
        if _subject_key(data["subject"]) != _subject_key(expected_subject):
            errors.append(f"{review.label}: review subject does not match execution output subject")
        for record_id in data["evidence_record_ids"]:
            record = evidence_records.get(record_id)
            if record is None:
                errors.append(f"{review.label}: unknown evidence_record_id {record_id}")
            elif (
                record.data["mission_id"] != data["mission_id"]
                or record.data["execution_id"] != data["execution_id"]
                or _subject_key(record.data["subject"]) != _subject_key(data["subject"])
            ):
                errors.append(f"{review.label}: evidence_record_id {record_id} belongs to another chain or subject")
        declared_evidence_ids = {
            item["evidence_id"]
            for record_id in data["evidence_record_ids"]
            if record_id in evidence_records
            for item in evidence_records[record_id].data["items"]
        }
        for assessment in data["criteria"]:
            if assessment["criterion_id"] not in criterion_ids[data["mission_id"]]:
                errors.append(f"{review.label}: unknown criterion_id {assessment['criterion_id']}")
            for evidence_id in assessment["evidence_ids"]:
                pair = evidence_items.get(evidence_id)
                if pair is None:
                    errors.append(f"{review.label}: unknown evidence_id {evidence_id}")
                elif evidence_id not in declared_evidence_ids:
                    errors.append(f"{review.label}: evidence_id {evidence_id} is not in a declared evidence record")
                elif assessment["criterion_id"] not in pair[1]["criterion_ids"]:
                    errors.append(f"{review.label}: evidence_id {evidence_id} is not bound to {assessment['criterion_id']}")
        assessed_ids = [item["criterion_id"] for item in data["criteria"]]
        if len(assessed_ids) != len(set(assessed_ids)):
            errors.append(f"{review.label}: criterion assessments must be unique")
        if set(assessed_ids) != criterion_ids[data["mission_id"]]:
            errors.append(f"{review.label}: review must assess every mission criterion exactly once")
        mission_criteria = {item["criterion_id"]: item for item in mission.data["success_criteria"]}
        if data["verdict"] == "PASS":
            for assessment in data["criteria"]:
                mission_criterion = mission_criteria.get(assessment["criterion_id"])
                if mission_criterion is None:
                    continue
                provided = []
                for evidence_id in assessment["evidence_ids"]:
                    pair = evidence_items.get(evidence_id)
                    if pair:
                        provided.append(pair[1])
                required_types = set(mission_criterion["required_evidence_types"])
                provided_types = {item["evidence_type"] for item in provided if item["result"] == "pass"}
                if not required_types.issubset(provided_types):
                    errors.append(f"{review.label}: {assessment['criterion_id']} lacks passing required evidence types {sorted(required_types - provided_types)}")
        risk = mission.data["risk"]
        provenance = data["provenance"]
        if provenance["worker_execution_ref"] != execution.data["worker_execution_id"]:
            errors.append(
                f"{review.label}: provenance worker_execution_ref does not match "
                "reviewed worker execution"
            )
        if risk["level"] in {"medium", "high"}:
            if provenance["runtime_ref"] == execution.data["worker_runtime_ref"]:
                errors.append(f"{review.label}: medium/high-risk review runtime must differ from worker runtime")
            if data["review_execution_id"] == execution.data["worker_execution_id"]:
                errors.append(f"{review.label}: medium/high-risk review execution must differ from worker execution")
            if not provenance["read_only"]:
                errors.append(f"{review.label}: medium/high-risk reviewer must be read-only")
            if provenance["access_mode"] != "read_only":
                errors.append(f"{review.label}: medium/high-risk review access_mode must be read_only")
        if provenance["access_mode"] == "read_write" and provenance["read_only"]:
            errors.append(f"{review.label}: read_write access_mode cannot claim read_only status")
        reviewed_at = _parse_time(data["reviewed_at"])
        running_times = [
            _parse_time(item["at"])
            for item in execution.data["state_history"]
            if item["state"] == "RUNNING"
        ]
        if running_times and reviewed_at < min(running_times):
            errors.append(f"{review.label}: review occurred before execution started")
        review_pending_times = [
            _parse_time(item["at"])
            for item in execution.data["state_history"]
            if item["state"] == "REVIEW_PENDING"
        ]
        if review_pending_times and reviewed_at < min(review_pending_times):
            errors.append(f"{review.label}: review occurred before REVIEW_PENDING")
        reviewed_evidence_ids = {
            evidence_id for assessment in data["criteria"] for evidence_id in assessment["evidence_ids"]
        }
        for evidence_id in reviewed_evidence_ids:
            pair = evidence_items.get(evidence_id)
            if pair and reviewed_at < _parse_time(pair[1]["captured_at"]):
                errors.append(f"{review.label}: evidence {evidence_id} was captured after review")
        if data["verdict"] == "PASS":
            check_time = as_of or _parse_time(data["reviewed_at"])
            if check_time > _parse_time(data["valid_until"]):
                errors.append(f"{review.label}: PASS review is stale at {check_time.isoformat()}")
            for evidence_id in reviewed_evidence_ids:
                pair = evidence_items.get(evidence_id)
                if pair and check_time > _parse_time(pair[1]["expires_at"]):
                    errors.append(f"{review.label}: evidence {evidence_id} is stale")
    for report in by_kind["final_report"]:
        data = report.data
        mission = missions.get(data["mission_id"])
        execution = executions.get(data["execution_id"])
        review = reviews.get(data["review_id"])
        if mission is None or execution is None or review is None:
            errors.append(f"{report.label}: final report references an unknown chain document")
            continue
        if execution.data["mission_id"] != data["mission_id"]:
            errors.append(f"{report.label}: report mission_id differs from its execution mission_id")
        if review.data["mission_id"] != data["mission_id"] or review.data["execution_id"] != data["execution_id"]:
            errors.append(f"{report.label}: report review belongs to another mission or execution")
        expected_judgment = VERDICT_TO_JUDGMENT[review.data["verdict"]]
        if data["judgment"] in set(VERDICT_TO_JUDGMENT.values()) and data["judgment"] != expected_judgment:
            errors.append(
                f"{report.label}: judgment {data['judgment']} conflicts with review verdict "
                f"{review.data['verdict']}"
            )
        if execution.data["current_state"] not in JUDGMENT_STATES[data["judgment"]]:
            errors.append(
                f"{report.label}: judgment {data['judgment']} conflicts with execution state "
                f"{execution.data['current_state']}"
            )
        if _subject_key(data["subject"]) != _subject_key(review.data["subject"]):
            errors.append(f"{report.label}: report subject differs from reviewed subject")
        unknown_criteria = set(data["verified_criterion_ids"]) - criterion_ids[data["mission_id"]]
        unknown_evidence = set(data["evidence_ids"]) - set(evidence_items)
        if unknown_criteria:
            errors.append(f"{report.label}: unknown verified criteria {sorted(unknown_criteria)}")
        if unknown_evidence:
            errors.append(f"{report.label}: unknown evidence IDs {sorted(unknown_evidence)}")
        declared_review_evidence = {
            item["evidence_id"]
            for record_id in review.data["evidence_record_ids"]
            if record_id in evidence_records
            for item in evidence_records[record_id].data["items"]
        }
        unreviewed_evidence = set(data["evidence_ids"]) - declared_review_evidence
        if unreviewed_evidence:
            errors.append(f"{report.label}: report cites evidence outside the reviewed records")
        for output in data["outputs"]:
            if _subject_key(output["subject"]) != _subject_key(data["subject"]):
                errors.append(f"{report.label}: output subject differs from report subject")
        if data["judgment"] == "PASSED":
            reviewed_criteria = {item["criterion_id"] for item in review.data["criteria"] if item["status"] == "satisfied"}
            reviewed_evidence = {evidence_id for item in review.data["criteria"] for evidence_id in item["evidence_ids"]}
            if set(data["verified_criterion_ids"]) != reviewed_criteria:
                errors.append(f"{report.label}: verified criteria must exactly match satisfied review criteria")
            if set(data["evidence_ids"]) != reviewed_evidence:
                errors.append(f"{report.label}: report evidence IDs must exactly match reviewed evidence IDs")
    return errors


def repository_document_paths() -> list[Path]:
    markdown = [
        path for path in ROOT.rglob("*.md")
        if not any(part in {".git", "node_modules", ".venv"} for part in path.parts)
    ]
    return sorted([*markdown, *ROOT.glob("templates/*.yaml")])


def validate_repository_documents() -> tuple[list[LoadedDocument], list[str]]:
    documents, errors = load_documents(repository_document_paths())
    errors.extend(validate_chain(documents))
    return documents, errors


def validate_local_links() -> list[str]:
    errors: list[str] = []
    link_re = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    paths = [
        path for path in ROOT.rglob("*.md")
        if not any(part in {".git", "node_modules", ".venv"} for part in path.parts)
    ]
    for path in sorted(paths):
        text = path.read_text(encoding="utf-8")
        for match in link_re.finditer(text):
            target = match.group(1).strip().split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = (path.parent / target).resolve()
            if not resolved.is_relative_to(ROOT) or not resolved.exists():
                line = text.count("\n", 0, match.start()) + 1
                errors.append(f"{path.relative_to(ROOT)}:{line}: broken or escaping local link: {target}")
    return errors


def load_sanitization_policy(path: Path = POLICY_PATH) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _allowed_ip(value: str, policy: dict[str, Any]) -> bool:
    try:
        address = ipaddress.ip_address(value.strip("[]"))
    except ValueError:
        return True
    networks = [ipaddress.ip_network(item) for item in policy["allowed_documentation_networks"]]
    return any(address in network for network in networks)


def sanitization_findings(label: str, text: str, policy: dict[str, Any] | None = None) -> list[str]:
    policy = policy or load_sanitization_policy()
    errors: list[str] = []
    for match in re.finditer(r"\b[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b", text):
        domain = match.group(1).lower()
        if not any(domain == item or domain.endswith("." + item) for item in policy["allowed_email_domains"]):
            errors.append(_finding(label, text, match.start(), "non-example email address"))
    for match in re.finditer(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?!\d|\.)(?![0-9a-f])", text):
        if not _allowed_ip(match.group(0), policy):
            errors.append(_finding(label, text, match.start(), "non-documentation IPv4 address"))
    for match in re.finditer(r"(?<![0-9A-Fa-f:])(?:[0-9A-Fa-f]{0,4}:){2,7}[0-9A-Fa-f]{0,4}(?![0-9A-Fa-f:])", text):
        candidate = match.group(0)
        if ":" in candidate and not _allowed_ip(candidate, policy):
            errors.append(_finding(label, text, match.start(), "non-documentation IPv6 address"))
    builtins = {
        "private POSIX path": r"(?<![A-Za-z0-9_.-])/(?:home|Users|root|private|var/(?:log|lib))/[A-Za-z0-9._~/-]+",
        "private Windows path": r"(?i)\b[A-Z]:\\(?:Users|Documents and Settings)\\[^\s'\"]+",
        "private hostname": r"(?i)\b[A-Za-z0-9][A-Za-z0-9-]{1,62}\.(?:internal|local)\b",
        "chat identifier": r"(?i)\b(?:chat|channel|room)[_-]?id\b\s*[:=]\s*['\"]?[-A-Z0-9]{6,}",
        "secret-shaped assignment": r"(?i)\b(?:api[_-]?key|secret|token|cookie|password|passwd|private[_-]?key)\b\s*[:=]\s*['\"]?(?!<|example|redacted|none|null|false|true)[A-Za-z0-9_./+=-]{8,}",
    }
    for name, pattern in {**builtins, **policy.get("patterns", {})}.items():
        for match in re.finditer(pattern, text):
            errors.append(_finding(label, text, match.start(), name))
    return errors


def _finding(label: str, text: str, position: int, reason: str) -> str:
    return f"{label}:{text.count(chr(10), 0, position) + 1}: {reason}"


def _git_lines(*args: str) -> list[str]:
    result = subprocess.run(["git", *args], cwd=ROOT, check=True, text=True, capture_output=True)
    return [line for line in result.stdout.splitlines() if line]


def _scan_texts(items: Iterable[tuple[str, str]], policy: dict[str, Any]) -> list[str]:
    excluded = set(policy.get("exclude_paths", []))
    extensions = set(policy["extensions"])
    errors: list[str] = []
    for label, text in items:
        base_label = label.split("@", 1)[0]
        if base_label in excluded or Path(base_label).suffix.lower() not in extensions:
            continue
        errors.extend(sanitization_findings(label, text, policy))
    return errors


def sanitization_scan(mode: str = "working-tree") -> list[str]:
    policy = load_sanitization_policy()
    if mode == "working-tree":
        paths = [p for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts and "node_modules" not in p.parts and ".venv" not in p.parts]
        items = ((str(path.relative_to(ROOT)), path.read_text(encoding="utf-8", errors="ignore")) for path in paths)
    elif mode == "tracked":
        items = ((rel, (ROOT / rel).read_text(encoding="utf-8", errors="ignore")) for rel in _git_lines("ls-files") if (ROOT / rel).is_file())
    elif mode == "history":
        objects: dict[str, str] = {}
        for line in _git_lines("rev-list", "--objects", "--all"):
            parts = line.split(" ", 1)
            if len(parts) == 2 and Path(parts[1]).suffix.lower() in set(policy["extensions"]):
                objects.setdefault(parts[0], parts[1])
        history_items: list[tuple[str, str]] = []
        for oid, rel in objects.items():
            result = subprocess.run(["git", "cat-file", "-p", oid], cwd=ROOT, text=True, capture_output=True, errors="ignore")
            if result.returncode == 0:
                history_items.append((f"{rel}@{oid[:12]}", result.stdout))
        items = history_items
    else:
        raise ValueError(f"unknown sanitization mode: {mode}")
    return _scan_texts(items, policy)
