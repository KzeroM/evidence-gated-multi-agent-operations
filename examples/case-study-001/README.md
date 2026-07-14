# Case Study 001: Reference Package Hardening

This fictional, public-safe case shows a medium-risk documentation hardening task. It remains a protocol example, not an orchestration implementation.

## Mission contract

```yaml
document_type: mission_contract
schema_version: "2.0"
mission_id: case-study-001
created_at: "2026-07-14T10:00:00Z"
objective: "Harden a fictional reference package with a coherent v2 evidence protocol."
non_goals: ["Build an agent runtime, scheduler, queue, or deployment engine."]
assumptions: ["All examples and identifiers are fictional and public-safe."]
success_criteria:
  - criterion_id: schemas-validate
    condition: "Every v2 document type validates in standalone and Markdown examples."
    required_evidence_types: [test_result]
  - criterion_id: public-gates-pass
    condition: "Public-safety, link, Markdown, and Mermaid gates pass."
    required_evidence_types: [command_result]
allowed_capabilities:
  filesystem:
    read: ["./**"]
    write: ["./schemas/**", "./egmo/**", "./tests/**", "./examples/**", "./*.md"]
  network:
    domains: ["registry.npmjs.org", "pypi.org"]
  deployment: false
  database_mutation: false
  messaging: false
output_ownership:
  owner: project
  expected_location: "repository root and named protocol directories"
  retention: project_lifetime
  retrieval_method: "Version control and validation logs."
target_subject:
  kind: git_commit
  algorithm: git-sha1
  value: "1111111111111111111111111111111111111111"
  locator: "https://example.org/fictional/reference/commit/1"
risk:
  level: medium
  production: false
approval:
  kind: explicit
  approval_id: case-approval-001
  approved_by: "human:fictional-maintainer"
  approved_at: "2026-07-14T10:05:00Z"
  scope: "Edit the fictional repository and run non-destructive validation."
```

## Execution record

```yaml
document_type: execution_record
schema_version: "2.0"
execution_id: case-execution-001
mission_id: case-study-001
idempotency_key: "case-study-001-attempt-1"
worker: "runtime:fictional-worker-v2"
worker_runtime_ref: "runtime:fictional-worker-v2"
worker_model_ref: "model:fictional-implementer-v2"
worker_execution_id: case-worker-run-001
environment_ref: "container:python-3.11-node-22"
input_subject:
  kind: git_commit
  algorithm: git-sha1
  value: "1111111111111111111111111111111111111111"
  locator: "https://example.org/fictional/reference/commit/1"
output_subject:
  kind: git_commit
  algorithm: git-sha1
  value: "2222222222222222222222222222222222222222"
  locator: "https://example.org/fictional/reference/commit/2"
current_state: PASSED
state_history:
  - state: DRAFT
    at: "2026-07-14T10:00:00Z"
    actor_ref: "service:fictional-controller"
  - state: APPROVED
    at: "2026-07-14T10:05:00Z"
    actor_ref: "human:fictional-maintainer"
  - state: RUNNING
    at: "2026-07-14T10:10:00Z"
    actor_ref: "runtime:fictional-worker-v2"
  - state: REVIEW_PENDING
    at: "2026-07-14T10:40:00Z"
    actor_ref: "service:fictional-controller"
  - state: PASSED
    at: "2026-07-14T11:00:00Z"
    actor_ref: "service:fictional-judge"
retry_policy:
  max_attempts: 2
  remaining_attempts: 1
timeout_seconds: 3600
attempt: 1
failure: null
cancellation: null
rollback_or_compensation: null
```

## Worker evidence

```yaml
document_type: evidence_record
schema_version: "2.0"
evidence_record_id: case-evidence-record-001
mission_id: case-study-001
execution_id: case-execution-001
producer: "runtime:fictional-worker-v2"
subject: &case_subject
  kind: git_commit
  algorithm: git-sha1
  value: "2222222222222222222222222222222222222222"
  locator: "https://example.org/fictional/reference/commit/2"
items:
  - evidence_id: case-test-evidence-001
    criterion_ids: [schemas-validate]
    evidence_type: test_result
    captured_at: "2026-07-14T10:35:00Z"
    expires_at: "2026-08-14T10:35:00Z"
    subject: *case_subject
    description: "The schema and cross-document suite passed."
    result: pass
    details:
      command: "python3 -m unittest discover -s tests -v"
      exit_status: 0
      started_at: "2026-07-14T10:34:00Z"
      ended_at: "2026-07-14T10:35:00Z"
      environment_ref: "container:python-3.11-node-22"
      output_artifact:
        uri: "https://example.org/artifacts/case-tests.txt"
        digest: "sha256:3333333333333333333333333333333333333333333333333333333333333333"
  - evidence_id: case-gates-evidence-001
    criterion_ids: [public-gates-pass]
    evidence_type: command_result
    captured_at: "2026-07-14T10:38:00Z"
    expires_at: "2026-08-14T10:38:00Z"
    subject: *case_subject
    description: "The public package gates completed successfully."
    result: pass
    details:
      command: "npm run validate && npm run lint:markdown && npm run lint:mermaid"
      exit_status: 0
      started_at: "2026-07-14T10:35:00Z"
      ended_at: "2026-07-14T10:38:00Z"
      environment_ref: "container:python-3.11-node-22"
      output_artifact:
        uri: "https://example.org/artifacts/case-gates.txt"
        digest: "sha256:4444444444444444444444444444444444444444444444444444444444444444"
known_limits:
  - "The case proves protocol structure, not correctness of every future adopter policy."
```

## Critic review

The official v2 schema has four verdicts. This review uses `PASS` because every criterion is satisfied and no must-fix item remains. A bounded improvement is represented as a structured deferral rather than inventing a fifth verdict.

```yaml
document_type: critic_review
schema_version: "2.0"
review_id: case-review-001
mission_id: case-study-001
execution_id: case-execution-001
evidence_record_ids: [case-evidence-record-001]
reviewed_at: "2026-07-14T10:50:00Z"
valid_until: "2026-08-14T10:50:00Z"
subject:
  kind: git_commit
  algorithm: git-sha1
  value: "2222222222222222222222222222222222222222"
  locator: "https://example.org/fictional/reference/commit/2"
reviewer: "runtime:fictional-reviewer-v2"
review_execution_id: case-review-run-001
provenance:
  runtime_ref: "runtime:fictional-reviewer-v2"
  model_ref: "model:fictional-critic-v2"
  worker_execution_ref: case-worker-run-001
  context_sources: ["https://example.org/review-packets/case-study-001"]
  context_scope: "Mission, diff, schemas, immutable evidence artifacts, and test output."
  access_mode: read_only
  read_only: true
  conflicts: []
verdict: PASS
criteria:
  - criterion_id: schemas-validate
    status: satisfied
    evidence_ids: [case-test-evidence-001]
    rationale: "The typed test result covers every supported document type."
  - criterion_id: public-gates-pass
    status: satisfied
    evidence_ids: [case-gates-evidence-001]
    rationale: "The command record covers sanitization, links, Markdown, and real Mermaid rendering."
findings: []
must_fix: []
deferrals:
  - description: "Add adopter-specific semantic policy only when a concrete integration needs it."
    accepted_by: "human:fictional-maintainer"
    expires_at: "2026-08-14T10:50:00Z"
```

## Final report

```yaml
document_type: final_report
schema_version: "2.0"
report_id: case-report-001
mission_id: case-study-001
execution_id: case-execution-001
review_id: case-review-001
subject:
  kind: git_commit
  algorithm: git-sha1
  value: "2222222222222222222222222222222222222222"
  locator: "https://example.org/fictional/reference/commit/2"
judgment: PASSED
summary: ["The fictional package now implements the evidence protocol and passes its gates."]
verified_criterion_ids: [schemas-validate, public-gates-pass]
evidence_ids: [case-test-evidence-001, case-gates-evidence-001]
changed_or_executed: ["Updated schemas, validation, examples, documentation, and CI checks."]
outputs:
  - uri: "https://example.org/artifacts/fictional-reference-v2"
    owner: "fictional reference project"
    retention: "project lifetime"
    retrieval: "Version control and release manifest."
    subject:
      kind: git_commit
      algorithm: git-sha1
      value: "2222222222222222222222222222222222222222"
      locator: "https://example.org/fictional/reference/commit/2"
remaining_risks: ["A passing structural protocol cannot prove the truth of unmodeled external claims."]
next_actions: []
```
