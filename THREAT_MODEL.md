# Threat Model

This reference package treats agent outputs, tool outputs, and generated artifacts as claims until they are verified. The model below names the threats that evidence gates are meant to reduce.

## Assets

- Mission contracts and success criteria
- Evidence artifacts: logs, diffs, screenshots, API responses, test output, read-backs
- Durable outputs: files, reports, generated documents, code, configuration
- Secrets and privileged state behind local or production boundaries
- Audit trail: who/what produced, reviewed, and judged each result

## Trust boundaries

| Boundary | What crosses it | Required control |
|---|---|---|
| Human request -> translator | Ambiguous intent, constraints, approvals | Mission contract with assumptions and non-goals |
| Web/tool output -> worker | Untrusted text, code, links, logs, package metadata | Treat as data; do not execute or obey embedded instructions blindly |
| Worker -> reviewer | Diffs, logs, self-reports, artifacts | Reviewer checks evidence against criteria, not confidence wording |
| Reviewer -> evidence judge | Findings and risk classification | Judge verifies closure or records accepted residual risk |
| Remote/sandbox -> local/privileged executor | Requests for local files, secrets, GUI, deployments, data mutation | Explicit local handoff, approval, rollback/stop condition |
| Artifacts -> public repository | Examples, logs, diagrams, docs | Sanitization scan and provenance notes |

## Threats and mitigations

| Threat | Failure mode | Mitigation |
|---|---|---|
| Prompt injection in retrieved content | Tool output tells an agent to ignore instructions, leak data, or alter scope | Treat external content as untrusted; cite it as evidence only after source and relevance checks |
| Untrusted command output | A failing command prints a misleading success message | Require exit status plus output; prefer independent read-back or test result |
| Self-certification | The worker declares completion without external proof | Separate worker, reviewer, and evidence judge responsibilities |
| Rubber-stamp review | Reviewer shares the worker's context, model, assumptions, or tool limitations | Require reviewer findings to name spec compliance, missing evidence, must-fix items, and risks |
| Artifact tampering | Evidence or generated files are changed after review | Record paths, hashes where appropriate, commit SHAs, and CI logs for durable outputs |
| Secret leakage | Logs, config, screenshots, or examples expose tokens, cookies, private URLs, local paths, or account IDs | Run sanitization search; redact secrets before publishing; never ask for secrets in chat |
| Wrong output ownership | Files are created in scratch paths and later lost or mistaken as canonical | Require owner, expected location, retention, and retrieval method before writing durable outputs |
| Boundary confusion | Remote sandbox claims local/production state was changed or verified | Mark local_required explicitly; use structured handoff or local execution report |
| Audit log loss | A final summary omits failed attempts, retries, or accepted risks | Final report must include changed/executed actions, verification evidence, residual risks, and next actions |
| Over-broad automation | Validator/CI executes untrusted generated code while checking docs | CI should parse/render/lint documents, not execute arbitrary snippets without review |

## Reviewer and evidence-judge independence

A review is stronger when at least one of these is true:

- The reviewer uses a separate model/runtime from the worker.
- The reviewer receives a compact mission packet plus artifacts, not the worker's full hidden reasoning.
- The reviewer has read-only access where possible.
- The evidence judge maps each success criterion to an artifact or command result instead of relying on reviewer sentiment.
- High-impact work has a second independent review or explicit user acceptance of residual risk.

A review is weak when the same agent that performed the work also writes the only review, or when the review says "looks good" without naming checked criteria and missing evidence.

## Minimum public-release controls

Before publishing examples or case studies:

1. Run the sanitization scan.
2. Verify schemas and example contracts.
3. Render or parse Mermaid diagrams.
4. Check local links.
5. Include a final report that names evidence and residual risk.
