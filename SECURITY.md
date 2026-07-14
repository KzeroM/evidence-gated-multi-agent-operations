# Security Policy

## Scope

This public repository contains a reference protocol, schemas, examples, and deterministic validation. It does not enforce runtime capabilities, authenticate provenance identities, execute agents, or operate deployments. The supported version is the latest default-branch commit.

## Reporting

Use private vulnerability reporting when available. If it is unavailable, open a minimal public issue requesting a private maintainer channel without sensitive details. Never include credentials, personal/private identifiers, private repository names, paths, hosts, chat IDs, topology, or evidence artifacts in a public report.

## Sensitive material response

1. Stop distributing the affected copy and avoid copying the value into issues or logs.
2. Preserve only minimal private investigation evidence.
3. Remove the material from the working tree and assess all reachable Git blobs.
4. Rotate any exposed credential through its owning system.
5. Re-run deterministic sanitization in working-tree, tracked, and history modes plus `detect-secrets`.
6. Bind an independent public-safety review to the repaired commit before publication.

The scanners are defense in depth. A clean scan cannot prove that all sensitive material has been omitted, and schema validity cannot prove evidence truth.
