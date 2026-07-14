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

from egmo.protocol import (
    ROOT,
    LoadedDocument,
    load_documents,
    validate_chain,
    validate_document,
    validate_document_semantics,
)


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


def mutable_template_chain() -> list[LoadedDocument]:
    return [LoadedDocument(copy.deepcopy(doc.data), doc.label) for doc in template_chain()]


class SchemaDispatchTests(unittest.TestCase):
    def test_normal_validation_emits_no_deprecation_warnings(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-W", "error",
                "-c",
                "from egmo.protocol import validate_document; "
                "assert validate_document({'schema_version': '2.0'})",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_every_supported_template_validates(self) -> None:
        docs = template_chain()
        self.assertEqual({doc.data["document_type"] for doc in docs}, {
            "mission_contract", "execution_record", "evidence_record", "critic_review", "final_report"
        })
        self.assertEqual(validate_chain(docs), [])

    def test_external_common_schema_ref_resolves_from_source_checkout(self) -> None:
        review = copy.deepcopy(document_of_type(template_chain(), "critic_review").data)
        review["review_id"] = "x"
        errors = validate_document(review, "source-ref")
        self.assertTrue(any("review_id" in item and "too short" in item for item in errors))

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

    def test_api_response_without_status_code_validates(self) -> None:
        evidence = copy.deepcopy(document_of_type(template_chain(), "evidence_record").data)
        item = evidence["items"][0]
        item["evidence_type"] = "api_response"
        item["details"] = {
            "source_uri": "https://example.org/api/results/example-request",
            "artifact": {
                "uri": "https://example.org/artifacts/example-api-response.json",
                "digest": f"sha256:{'d' * 64}",
            },
        }
        self.assertEqual(validate_document(evidence), [])
        self.assertEqual(validate_document_semantics(LoadedDocument(evidence, "api-response")), [])

    def test_artifact_and_read_back_details_validate(self) -> None:
        for evidence_type in ("artifact", "read_back"):
            with self.subTest(evidence_type=evidence_type):
                evidence = copy.deepcopy(document_of_type(template_chain(), "evidence_record").data)
                item = evidence["items"][0]
                item["evidence_type"] = evidence_type
                self.assertEqual(validate_document(evidence), [])
                self.assertEqual(
                    validate_document_semantics(LoadedDocument(evidence, evidence_type)), []
                )

    def test_artifact_and_read_back_reject_command_details(self) -> None:
        for evidence_type in ("artifact", "read_back"):
            with self.subTest(evidence_type=evidence_type):
                evidence = copy.deepcopy(document_of_type(template_chain(), "evidence_record").data)
                item = evidence["items"][1]
                item["evidence_type"] = evidence_type
                self.assertTrue(validate_document(evidence))
                errors = validate_document_semantics(LoadedDocument(evidence, evidence_type))
                self.assertTrue(any("requires artifact/read-back details" in error for error in errors))


class EndToEndNegativeTests(unittest.TestCase):
    def mutate(self) -> list[LoadedDocument]:
        return mutable_template_chain()

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

    def test_post_review_output_mutation_invalidates_pass(self) -> None:
        docs = self.mutate()
        execution = document_of_type(docs, "execution_record")
        execution.data["output_subject"]["value"] = "f" * 40
        errors = validate_chain(docs)
        self.assertTrue(any("evidence subject does not match" in item for item in errors))
        self.assertTrue(any("review subject does not match" in item for item in errors))

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
        self.assertTrue(any("medium/high-risk review runtime must differ" in item for item in errors))
        self.assertTrue(any("medium/high-risk review execution must differ" in item for item in errors))

    def test_medium_risk_non_independence_and_write_access_fail(self) -> None:
        docs = self.mutate()
        execution = document_of_type(docs, "execution_record")
        review = document_of_type(docs, "critic_review")
        review.data["provenance"]["runtime_ref"] = execution.data["worker_runtime_ref"]
        review.data["review_execution_id"] = execution.data["worker_execution_id"]
        review.data["provenance"]["access_mode"] = "read_write"
        review.data["provenance"]["read_only"] = False
        errors = validate_chain(docs)
        self.assertTrue(any("medium/high-risk review runtime must differ" in item for item in errors))
        self.assertTrue(any("medium/high-risk review execution must differ" in item for item in errors))
        self.assertTrue(any("medium/high-risk reviewer must be read-only" in item for item in errors))
        self.assertTrue(any("medium/high-risk review access_mode must be read_only" in item for item in errors))

    def test_report_cannot_overrule_review(self) -> None:
        docs = self.mutate()
        review = next(doc for doc in docs if doc.data["document_type"] == "critic_review")
        review.data["verdict"] = "REQUEST_CHANGES"
        review.data["criteria"][0]["status"] = "not_satisfied"
        review.data["must_fix"] = ["Correct the fictional artifact."]
        self.assertTrue(any("conflicts with review verdict" in item for item in validate_chain(docs)))

    def test_review_cannot_borrow_another_execution_evidence(self) -> None:
        docs = self.mutate()
        evidence = document_of_type(docs, "evidence_record")
        evidence.data["execution_id"] = "other-execution"
        errors = validate_chain(docs)
        self.assertTrue(any("belongs to another chain or subject" in item for item in errors))

    def test_review_cannot_precede_evidence_capture(self) -> None:
        docs = self.mutate()
        review = document_of_type(docs, "critic_review")
        review.data["reviewed_at"] = "2026-07-14T09:20:00Z"
        errors = validate_chain(docs)
        self.assertTrue(any("captured after review" in item for item in errors))

    def test_report_output_must_match_reviewed_subject(self) -> None:
        docs = self.mutate()
        report = document_of_type(docs, "final_report")
        report.data["outputs"][0]["subject"]["value"] = "f" * 40
        errors = validate_chain(docs)
        self.assertTrue(any("output subject differs" in item for item in errors))

    def test_invalid_state_transition_fails(self) -> None:
        docs = self.mutate()
        execution = document_of_type(docs, "execution_record")
        execution.data["state_history"][1]["state"] = "PASSED"
        errors = validate_chain(docs)
        self.assertTrue(any("invalid state transition DRAFT -> PASSED" in item for item in errors))

    def test_cancelled_state_requires_cancellation_metadata(self) -> None:
        execution = copy.deepcopy(document_of_type(template_chain(), "execution_record").data)
        execution["current_state"] = "CANCELLED"
        execution["state_history"][-1]["state"] = "CANCELLED"
        errors = validate_document_semantics(LoadedDocument(execution, "cancelled"))
        self.assertTrue(any("requires cancellation metadata" in item for item in errors))

    def test_verdict_semantics_are_enforced(self) -> None:
        review = copy.deepcopy(document_of_type(template_chain(), "critic_review").data)
        review["verdict"] = "INCONCLUSIVE"
        errors = validate_document_semantics(LoadedDocument(review, "inconclusive"))
        self.assertTrue(any("requires an insufficient_evidence criterion" in item for item in errors))

    def test_inconclusive_chain_is_coherent_but_not_passed(self) -> None:
        docs = self.mutate()
        execution = document_of_type(docs, "execution_record")
        review = document_of_type(docs, "critic_review")
        report = document_of_type(docs, "final_report")
        execution.data["current_state"] = "EVIDENCE_PENDING"
        execution.data["state_history"][-1]["state"] = "EVIDENCE_PENDING"
        review.data["verdict"] = "INCONCLUSIVE"
        review.data["criteria"][0]["status"] = "insufficient_evidence"
        report.data["judgment"] = "INCONCLUSIVE"
        self.assertEqual(validate_chain(docs), [])

    def test_review_worker_execution_reference_must_match(self) -> None:
        docs = self.mutate()
        review = next(doc for doc in docs if doc.data["document_type"] == "critic_review")
        review.data["provenance"]["worker_execution_ref"] = "different-worker-run"
        errors = validate_chain(docs)
        self.assertTrue(any("worker_execution_ref does not match" in item for item in errors))

    def test_pass_review_with_unknown_criterion_fails_without_exception(self) -> None:
        docs = self.mutate()
        review = next(doc for doc in docs if doc.data["document_type"] == "critic_review")
        review.data["criteria"][0]["criterion_id"] = "unknown-criterion"
        errors = validate_chain(docs)
        self.assertTrue(any("unknown criterion_id unknown-criterion" in item for item in errors))


class CliTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "egmo.cli", *args], cwd=ROOT, text=True, capture_output=True
        )

    def test_judge_passes_complete_template_chain(self) -> None:
        result = self.run_cli("judge", *(str(path) for path in TEMPLATE_PATHS))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASSED", result.stdout)

    def test_unknown_review_criterion_exits_one_without_traceback(self) -> None:
        docs = mutable_template_chain()
        review = next(doc for doc in docs if doc.data["document_type"] == "critic_review")
        review.data["criteria"][0]["criterion_id"] = "unknown-criterion"
        with tempfile.TemporaryDirectory() as directory:
            paths = []
            for index, doc in enumerate(docs):
                path = Path(directory) / f"{index}-{doc.data['document_type']}.yaml"
                path.write_text(yaml.safe_dump(doc.data, sort_keys=False), encoding="utf-8")
                paths.append(str(path))
            result = self.run_cli("judge", *paths)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("unknown criterion_id unknown-criterion", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_judge_usage_error_is_two(self) -> None:
        result = self.run_cli("judge")
        self.assertEqual(result.returncode, 2)

    def test_judge_rejects_timezone_less_as_of_without_traceback(self) -> None:
        result = self.run_cli(
            "judge", *(str(path) for path in TEMPLATE_PATHS), "--as-of", "2026-07-14T12:00:00"
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("UTC offset", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

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
