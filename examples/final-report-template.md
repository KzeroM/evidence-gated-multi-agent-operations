# Final Report Template

Use [`templates/final-report.yaml`](../templates/final-report.yaml) as the canonical v2 final report. It is schema validated and binds judgment, criterion IDs, evidence IDs, and outputs to the same immutable subject as the review.

A final report does not create a pass. `PASSED` is valid only when the referenced execution is in `PASSED`, the review verdict is `PASS`, every criterion is satisfied, referenced evidence is fresh, and the subject is unchanged.

Avoid reports that only say `done`, `fixed`, or `looks good`.
