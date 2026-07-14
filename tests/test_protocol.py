"""Unit and end-to-end regression tests for EGMO v2."""

from __future__ import annotations

import copy
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

import yaml

from egmo.protocol import ROOT, LoadedDocument, load_documents, validate_chain, validate_document


TEMPLATE_PATHS = [
    ROOT / "templates" / name
    for name in (
        "mission.yaml",
        "execution-record.yaml",
        "evidence.yaml",
        "critic-review.yaml",
        "final-report.yaml",
    )
]


def template_chain() -> list[LoadedDocument]:
    docs, errors = load_documents(TEMPLATE_PATHS)
    if errors:
        raise AssertionError(errors)
    return docs


def document_of_type(documents: list[LoadedDocument], document_type: str) -> LoadedDocument:
    return next(doc for doc in documents if doc.data["document_type"] == document_type)


class SchemaDispatchTests(unittest.TestCase):
    def test_every_supported_template_validates(self) -> None:
        docs = template_chain()
        self.assertEqual({doc.data["document_type"] for doc in docs}, {
            "mission_contract", "execution_record", "evidence_record", "critic_review", "final_report"
        })
        self.assertEqual(validate_chain(docs), [])

    def test_missing_discriminator_is_rejected(self) -> None:
        self.assertTrue(validate_document({"schema_version": "2.0"})[0].endswith(
            "must declare document_type and schema_version"
        ))

    def test_unknown_properties_are_rejected(self) -> None:
        mission = copy.deepcopy(document_of_type(template_chain(), "mission_contract").data)
        mission["surprise"] = True
        self.assertTrue(any("Additional properties" in item for item in validate_document(mission)))

    def test_bad_format_is_rejected(self) -> None:
        mission = copy.deepcopy(document_of_type(template_chain(), "mission_contract").data)
        mission["created_at"] = "yesterday"
        self.assertTrue(any("date-time" in item for item in validate_document(mission)))

    def test_subject_kind_algorithm_pair_is_rejected(self) -> None:
        mission = copy.deepcopy(document_of_type(template_chain(), "mission_contract").data)
        mission["target_subject"]["algorithm"] = "sha256"
        mission["target_subject"]["value"] = "f" * 64
        self.assertTrue(any("not valid for subject kind" in item for item in validate_document(mission)))


class EndToEndNegativeTests(unittest.TestCase):
    def mutate(self) -> list[LoadedDocument]:
        return [LoadedDocument(copy.deepcopy(doc.data), doc.label) for doc in template_chain()]

    def test_unknown_criterion_reference_fails(self) -> None:
        docs = self.mutate()
        evidence = next(doc for doc in docs if doc.data["document_type"] == "evidence_record")
        evidence.data["items"][0]["criterion_ids"] = ["missing-criterion"]
        self.assertTrue(any("unknown criteria" in item for item in validate_chain(docs)))

    def test_tampered_subject_fails(self) -> None:
        docs = self.mutate()
        review = next(doc for doc in docs if doc.data["document_type"] == "critic_review")
        review.data["subject"]["value"] = "f" * 40
        self.assertTrue(any("review subject" in item for item in validate_chain(docs)))

    def test_stale_evidence_invalidates_pass(self) -> None:
        docs = self.mutate()
        errors = validate_chain(docs, as_of=datetime.fromisoformat("2026-09-01T00:00:00+00:00"))
        self.assertTrue(any("stale" in item for item in errors))

    def test_pass_with_unsatisfied_criterion_fails(self) -> None:
        docs = self.mutate()
        review = next(doc for doc in docs if doc.data["document_type"] == "critic_review")
        review.data["criteria"][0]["status"] = "insufficient_evidence"
        self.assertTrue(any("PASS requires" in item for item in validate_chain(docs)))

    def test_high_risk_non_independence_fails(self) -> None:
        docs = self.mutate()
        mission = next(doc for doc in docs if doc.data["document_type"] == "mission_contract")
        execution = next(doc for doc in docs if doc.data["document_type"] == "execution_record")
        review = next(doc for doc in docs if doc.data["document_type"] == "critic_review")
        mission.data["risk"] = {"level": "high", "production": True}
        mission.data["approval"]["expires_at"] = "2026-07-20T09:05:00Z"
        mission.data["rollback_or_compensation_plan"] = "file://plans/example-rollback.md"
        review.data["provenance"]["runtime_ref"] = execution.data["worker_runtime_ref"]
        review.data["review_execution_id"] = execution.data["worker_execution_id"]
        errors = validate_chain(docs)
        self.assertTrue(any("runtime must differ" in item for item in errors))
        self.assertTrue(any("execution must differ" in item for item in errors))

    def test_report_cannot_overrule_review(self) -> None:
        docs = self.mutate()
        review = next(doc for doc in docs if doc.data["document_type"] == "critic_review")
        review.data["verdict"] = "REQUEST_CHANGES"
        review.data["criteria"][0]["status"] = "not_satisfied"
        review.data["must_fix"] = ["Correct the fictional artifact."]
        self.assertTrue(any("PASSED judgment requires PASS" in item for item in validate_chain(docs)))


class CliTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "egmo.cli", *args], cwd=ROOT, text=True, capture_output=True
        )

    def test_judge_passes_complete_template_chain(self) -> None:
        result = self.run_cli("judge", *(str(path) for path in TEMPLATE_PATHS), "--as-of", "2026-07-15T00:00:00Z")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASSED", result.stdout)

    def test_judge_usage_error_is_two(self) -> None:
        result = self.run_cli("judge")
        self.assertEqual(result.returncode, 2)

    def test_create_task_is_non_executing_scaffold(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "packet"
            result = self.run_cli("create-task", str(output), "--mission-id", "fictional-task-0002")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(list(output.glob("*.yaml"))), 5)
            mission = yaml.safe_load((output / "mission.yaml").read_text(encoding="utf-8"))
            self.assertEqual(mission["mission_id"], "fictional-task-0002")
            docs, errors = load_documents(output.glob("*.yaml"))
            self.assertEqual(errors, [])
            self.assertEqual(validate_chain(docs), [])


if __name__ == "__main__":
    unittest.main()
