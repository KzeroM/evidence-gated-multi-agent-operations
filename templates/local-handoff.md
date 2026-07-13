# Local Handoff Template

Use this only when a mission explicitly requires execution across a local or privileged trust boundary. Keep the handoff bounded; it does not grant permission to widen scope.

## Mission and purpose

- Mission reference: `example-mission-0001`
- Purpose: run the named local check and return only the evidence fields below.
- Stop condition: stop on the first unexpected side effect, missing prerequisite, or request for a forbidden input.

## Allowed inputs

- The named project checkout.
- Fictional or already-public test data.

## Forbidden inputs and actions

- Credentials, private task history, or unrelated local files.
- Production mutation, deployment, messaging, or destructive commands.
- Any action not explicitly listed under **Authorized command**.

## Authorized command

```bash
npm run validate
```

## Output ownership

- Owner: artifact store
- Expected location: the mission's evidence directory
- Retention: task artifact
- Retrieval method: evidence manifest and final report

## Required return

```yaml
mission_ref: "example-mission-0001"
intent: "Run the bounded local validation."
command: "npm run validate"
exit_status: 0
result_summary: "Validation passed."
artifacts: []
unexpected_side_effects: []
remaining_limits: []
```
