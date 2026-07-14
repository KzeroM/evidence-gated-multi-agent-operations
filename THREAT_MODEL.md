# Threat Model

This reference protocol treats worker output, tool output, reviews, and generated artifacts as claims until they are validated against an immutable subject. It defines records and gates; it does not provide runtime isolation or capability enforcement.

## Assets and boundaries

Assets include mission/approval contracts, stable criteria, execution history, evidence artifacts, reviewer provenance, durable outputs, secrets behind privileged boundaries, rollback records, and the final audit chain.

| Boundary | Threat | Required protocol control |
| --- | --- | --- |
| Human intent to mission | Ambiguous scope or fabricated approval | Explicit objective, non-goals, capabilities, risk, approver, scope, time, and expiry where required |
| Untrusted input to remotely managed worker | Prompt injection or malicious tool/package output | Treat content as data; grant only declared filesystem/network/mutation capabilities |
| Worker to evidence store | Misleading output, lost failure, or self-certification | Typed result, exit status/timing/environment, immutable artifact digest, failure classification |
| Evidence to reviewer | Tampering or stale proof | Exact subject equality, SHA/version binding, evidence expiry, read-back where appropriate |
| Worker to reviewer | Shared assumptions or rubber stamp | Reviewer identity/runtime/model, separate execution, context scope/sources, access mode, conflicts |
| Remote to trusted/privileged executor | Boundary confusion or excess authority | Scoped approval, idempotency/timeout/stop conditions, typed returned evidence, rollback reference |
| Reviewed artifact to final report | Post-review mutation or overruled verdict | Subject equality, review validity, evidence freshness, criterion/evidence ID references |
| Repository to public | Secret or private topology disclosure | Configurable tree/tracked/history scanning plus a standard secret scanner and independent review |

VPS-first is one deployment profile for the remotely managed boundary. The same controls apply to managed CI, hosted agents, local sandboxes, human workflows, and other vendors.

## Threats and mitigations

| Threat | Failure mode | Mitigation |
| --- | --- | --- |
| Prompt injection | Retrieved content requests scope expansion or disclosure | Never treat retrieved instructions as authority; preserve mission capability limits |
| False command success | Output text says success despite failure | Record command, numeric exit status, start/end time, environment, and output artifact digest |
| Copied criterion prose | Evidence silently changes the meaning of a criterion | Reference stable `criterion_id` values defined by the mission |
| Artifact tampering | File or deployment changes after evidence capture | Bind every stage to a typed digest/version; mutation creates a new subject and invalidates prior pass |
| Stale proof | Old evidence is reused after dependencies or state change | Enforce `expires_at` and `valid_until` at judgment time |
| Reviewer non-independence | The worker reviews its own high-impact result | High risk requires separate runtime and execution plus read-only review; all levels disclose provenance |
| Approval laundering | A broad or expired approval is reused | Medium requires explicit approval; high/production requires scoped expiring approval and rollback/compensation |
| Over-broad side effects | Prose authorization is interpreted expansively | Machine-checkable filesystem globs, network domains, and mutation flags |
| Partial success hidden | Some changes occur before failure | State, retry budget, failure classification, cancellation, and rollback/compensation records |
| Failed privileged handoff | Transport acknowledgment is treated as execution | Require returned typed evidence; otherwise record `BLOCKED`/`PARTIAL_SUCCESS` and do not pass |
| Secret leakage | Keys, paths, hosts, account IDs, or topology enter public files/history | Scan broad file types, Windows/POSIX paths, IPv4/IPv6, environment-shaped secrets, tracked files and blobs |
| Validator overreach | A docs checker becomes an execution engine | Parse documents and render diagrams only; never execute fenced task commands or schedule workers |

## Review admissibility and verdicts

`PASS` means all criteria are satisfied by referenced, fresh evidence for the exact reviewed subject and no must-fix item remains. `REQUEST_CHANGES` requires a correctable must-fix item. `BLOCKED` names unavailable authority/dependency/boundary access. `INCONCLUSIVE` means evidence cannot justify pass or a specific correction.

A deferral is not a partial pass. Under `PASS`, it may describe a bounded future improvement only when it does not leave a success criterion unsatisfied; it records an accepting identity and expiry. Otherwise the verdict must not be `PASS`.

## Residual risks

- JSON Schema and deterministic checks establish structure and relationships, not factual truth.
- A declared capability grant must still be enforced by a sandbox, access-control system, or human procedure.
- Identity and model references require an external identity/audit system to prove authenticity.
- Pattern and standard secret scanners can miss novel secrets and can report false positives.
- A valid digest proves identity only if capture and storage mechanisms are trustworthy.

## Minimum public-release controls

Run schema/cross-document validation, unit and negative tests, working-tree/tracked/history sanitization, a standard secret scan, real Mermaid rendering (including malformed-input regression), Markdown lint, local-link checks, package smoke tests, and an independent review of the exact immutable subject.
