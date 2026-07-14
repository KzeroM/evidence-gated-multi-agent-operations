# Mission Contract Examples

The canonical v2 mission example is [`templates/mission.yaml`](../templates/mission.yaml). It demonstrates stable criterion IDs, an immutable Git subject, explicit medium-risk approval, output ownership, and machine-checkable capabilities.

Adapt the capability grant narrowly:

| Task | Typical capability change |
| --- | --- |
| Documentation | Repository read plus writes to named documentation globs |
| Source change | Reads for the project and writes only to owned source/test globs |
| API read-back | Add only the exact public or approved API domains |
| Deployment | Set `deployment: true`, classify high/production risk, add expiring approval and rollback plan |

Do not copy a template approval into a real mission. The approver, scope, timestamp, and expiry are facts about the particular contract.

The complete Markdown example is [`case-study-001/README.md`](case-study-001/README.md).
