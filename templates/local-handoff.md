# Privileged-Boundary Handoff Template

Use this only when a mission explicitly authorizes a transition from an untrusted/remotely managed execution boundary to a trusted or privileged boundary. A transport acknowledgment is not evidence of execution.

The packet must contain:

- mission and execution IDs plus immutable input subject;
- exact capability subset and approval ID;
- authorized commands or actions and timeout;
- idempotency key, stop conditions, and cancellation contact;
- expected typed evidence and owned artifact location;
- rollback or compensation reference for high-impact work.

The privileged executor returns a conforming [`evidence_record`](evidence.yaml) and updated [`execution_record`](execution-record.yaml). If the local handoff fails, record a classified failure and `BLOCKED`, `PARTIAL_SUCCESS`, or `ROLLBACK_PENDING`; never synthesize successful evidence.
