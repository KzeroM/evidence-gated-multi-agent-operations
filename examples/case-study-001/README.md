# Case Study 001: Public Reference Package Hardening

This case study shows the pattern applied to this repository. It is intentionally small and public-safe: the task is to harden a document-only reference package with machine-checkable contracts and CI.

## 1. Request

```text
Review feedback says the package is a strong operating philosophy, but it needs schemas, examples, CI, and a threat model so the evidence gate is applied to the repository itself.
```

## 2. Mission contract

```yaml
mission:
  objective: "Harden the public reference package so its mission contracts, final reports, examples, and public-release checks are machine-checkable."
  non_goals:
    - "Build a full orchestration platform or agent runtime."
    - "Add private operational names, chat IDs, credentials, or machine-specific paths."
  assumptions:
    - "The repository remains a vendor-neutral documentation/reference package."
    - "CI may use common open-source linting and validation tools."
  success_criteria:
    - criterion: "Mission contracts and final reports have machine-checkable structure."
      required_evidence: "JSON Schema files exist and sample YAML validates against them."
    - criterion: "The repository demonstrates an end-to-end evidence-gated flow."
      required_evidence: "A case study includes request, mission contract, worker evidence, reviewer findings, judge decision, and final report."
    - criterion: "Public-release risks are named."
      required_evidence: "Threat model covers prompt injection, untrusted tool output, artifact tampering, secret leakage, and reviewer independence."
    - criterion: "Validation can run automatically."
      required_evidence: "CI workflow runs schema/example validation, Markdown linting, link checks, Mermaid rendering, and sanitization scan."
  allowed_side_effects:
    - "Add schemas, scripts, documentation, examples, and CI files to the repository."
    - "Run local validation commands."
  output_ownership:
    owner: "project"
    expected_location: "repository root, schemas/, scripts/, examples/case-study-001/, and .github/workflows/"
    retention: "project lifetime"
    retrieval_method: "git history, README links, and CI logs"
  local_required: false
  risk_level: medium
```

## 3. Worker evidence

| Evidence item | What it proves |
|---|---|
| `schemas/mission-contract.schema.json` | Mission contracts have required fields, evidence criteria, ownership, local boundary, and risk level. |
| `schemas/final-report.schema.json` | Final reports must include summary, verification evidence, changed/executed actions, outputs, risks, and next actions. |
| `scripts/validate.py` | Example YAML, schema files, and sanitization patterns can be checked locally and in CI. |
| `.github/workflows/validate.yml` | The repository applies automated checks on pull requests and pushes. |
| `THREAT_MODEL.md` | Security and independence risks are explicit instead of implicit. |

## 4. Reviewer findings

```yaml
critic_verdict: PASS_WITH_DEFERRALS
spec_compliance:
  - "Schemas cover the current mission and final report templates."
  - "Case study maps request through judge decision and final report."
  - "Threat model includes the named risks and reviewer independence criteria."
missing_evidence:
  - "A full CLI validator with packaged dependencies is not included."
risks:
  - "Markdown lint/link/Mermaid checks depend on CI tools being available."
  - "Schemas enforce structure, not semantic truthfulness of evidence."
must_fix: []
can_defer:
  - "Package the validator as a CLI if external adopters need local installation."
  - "Add more pass/fail evidence examples for additional task types."
```

## 5. Evidence judge decision

| Criterion | Decision | Evidence |
|---|---|---|
| Machine-checkable structure | Pass | `schemas/*.schema.json`, `scripts/validate.py` |
| End-to-end flow | Pass | This case study contains request, contract, evidence, review, decision, and report |
| Public-release risks | Pass | `THREAT_MODEL.md` |
| Automatic validation | Pass with CI dependency | `.github/workflows/validate.yml` |

Residual risk: schemas and CI reduce drift but cannot prove that evidence is true. Human or independent-agent judgment is still required for high-impact work.

## 6. Final report

```yaml
summary:
  - "The reference package now has schema-backed examples, a threat model, a validation script, and CI checks."
verified:
  - evidence: "JSON Schema validation for mission and final-report examples"
    result: "Examples conform to the documented structure."
  - evidence: "Sanitization scan"
    result: "Public files are checked for obvious private-operation identifiers and secret-shaped assignments."
changed_or_executed:
  - "Added mission contract and final report schemas."
  - "Added repository validation script."
  - "Added public-safe case study."
  - "Added CI workflow for validation, Markdown, links, Mermaid, and sanitization."
outputs:
  - path_or_url: "schemas/mission-contract.schema.json"
    owner: "project"
    retention: "project lifetime"
    retrieval: "Git path and README repository contents table"
  - path_or_url: "examples/case-study-001/README.md"
    owner: "project"
    retention: "project lifetime"
    retrieval: "Git path and README repository contents table"
remaining_risks:
  - "CI tooling availability may differ across environments."
  - "Schema validation checks structure, not the factual truth of evidence claims."
next_actions_if_needed:
  - "Add more case studies for code changes, local-only tasks, and API integrations if adoption requires them."
```
