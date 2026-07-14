# Complete Protocol Chain

[`case-study-001/README.md`](case-study-001/README.md) contains the complete v2 chain as five machine-checkable fenced YAML documents: mission, execution, evidence, critic review, and final report. The repository validator dispatches each block by `document_type` and validates both its schema and its cross-document references.

The standalone copies under [`templates/`](../templates/) form a second complete chain suitable for `egmo judge` smoke testing.
