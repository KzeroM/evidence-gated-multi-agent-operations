# Example Mission Contracts

These examples are intentionally generic. Replace paths, evidence requirements, and risk levels with the values appropriate to your environment.

---

## Public reference document

```yaml
mission:
  objective: "Create a public reference README for an AI operations architecture."
  non_goals:
    - "Expose private agent names, chat IDs, credentials, paths, or provider-specific internals."
  assumptions:
    - "The target audience wants a reusable pattern, not a private operations manual."
  success_criteria:
    - criterion: "README explains the pattern clearly."
      required_evidence: "Readable Markdown with diagrams, roles, gates, examples, and security notes."
    - criterion: "No private/internal names are present."
      required_evidence: "Sanitization search returns zero matches for the internal-name list."
    - criterion: "The draft can be reused later."
      required_evidence: "File is stored in an indexed artifact or project location with manifest/verification notes."
  allowed_side_effects:
    - "Write Markdown and Mermaid files under the chosen artifact or project path."
    - "Rebuild the artifact/search index."
  output_ownership:
    owner: "artifact store"
    expected_location: "artifacts/<date>/<task-id>/files/public-architecture/README.md"
    retention: "long-term reference"
    retrieval_method: "artifact index search"
  local_required: false
  risk_level: low
```

---

## Code change with review

```yaml
mission:
  objective: "Fix a bug in a project and verify the fix."
  non_goals:
    - "Rewrite unrelated modules."
    - "Change production configuration."
  assumptions:
    - "The bug is reproducible with a targeted test or smoke command."
  success_criteria:
    - criterion: "Bug is reproduced before the fix."
      required_evidence: "Failing test, log, or minimal reproduction."
    - criterion: "Bug is fixed with minimal targeted change."
      required_evidence: "Diff summary and passing targeted test."
    - criterion: "No obvious regression is introduced."
      required_evidence: "Relevant smoke test or existing test subset passes."
  allowed_side_effects:
    - "Modify files in the project workspace."
    - "Run local tests and linters."
  output_ownership:
    owner: "project"
    expected_location: "project repository"
    retention: "project lifetime"
    retrieval_method: "git diff, test logs, artifact verification notes"
  local_required: false
  risk_level: medium
```
