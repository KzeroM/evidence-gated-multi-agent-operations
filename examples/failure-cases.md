# Failure-Centered Examples

These fictional scenarios describe the required protocol outcome. They are deliberately not passing document packets.

| Scenario | Evidence-centered handling | Expected state/verdict |
| --- | --- | --- |
| Insufficient evidence | A test claim lacks its command result or output artifact; the review marks the criterion `insufficient_evidence` | `EVIDENCE_PENDING` / `INCONCLUSIVE` |
| Tampered artifact | The read-back SHA-256 differs from the evidence digest, so the current subject is not the reviewed subject | `CHANGES_REQUESTED` / `REQUEST_CHANGES` |
| Stale artifact | Evidence or review is past `expires_at`/`valid_until` at judgment time | `EVIDENCE_PENDING` / `INCONCLUSIVE` |
| Non-independent reviewer | A high-risk review reuses the worker runtime or worker execution reference | validation failure; no admissible verdict |
| Failed privileged handoff | The boundary executor rejects the approval or cannot return artifacts; the failure is classified and not hidden | `BLOCKED` / `BLOCKED` |
| Partial change and rollback | Some side effects occurred before a non-retryable failure; compensation evidence is collected | `ROLLBACK_PENDING`, then `ROLLED_BACK` |
| Post-review mutation | A file, commit, OCI digest, deployment revision, or resource version changes after review | prior `PASS` invalid; create new evidence and review |

These outcomes are checked in negative end-to-end tests, including bad references, stale evidence, changed subjects, and non-independent high-risk review.

## Fictional protocol traces

- **Insufficient evidence:** `fictional-mission-a` requires a `test_result`, but its evidence record contains only an artifact description. Criterion `tests-pass` is marked `insufficient_evidence`; the review is `INCONCLUSIVE`, and the execution returns to `EVIDENCE_PENDING`.
- **Tampered or stale artifact:** `fictional-file-evidence-a` names one SHA-256 digest, while read-back observes another. Even if the digest matched, judgment after its `expires_at` would reject the prior proof. Both cases require fresh evidence for the newly observed subject.
- **Non-independent review:** a fictional high-risk deployment packet reports the same runtime and execution reference for worker and reviewer. Cross-document validation rejects the review before its verdict can be admitted.
- **Failed local handoff:** a fictional privileged executor cannot match the approval scope to the requested capability. It records a permission-classified failure and `BLOCKED`; a transport acknowledgment is not converted into success evidence.
- **Rollback:** a fictional write partially succeeds and the following dependency fails. The record moves through `PARTIAL_SUCCESS` and `ROLLBACK_PENDING`; only typed compensation evidence plus a completed rollback reference permits `ROLLED_BACK`.
- **Post-review mutation:** a reviewed commit, file digest, image digest, deployment revision, or resource version changes. Subject equality fails, so the old review and final report cannot pass the new subject.
