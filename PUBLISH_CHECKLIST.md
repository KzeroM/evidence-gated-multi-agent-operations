# Publish Checklist

## Protocol and content

- [ ] English and Korean READMEs describe the same v2 protocol and boundary model.
- [ ] The package is still a reference protocol, not an orchestration/runtime implementation.
- [ ] Every fenced YAML document declares a supported type and version and validates.
- [ ] Mission, execution, evidence, review, and report examples form a valid ID-linked chain.
- [ ] Risk approval, capabilities, immutable subjects, freshness, and reviewer provenance are present.
- [ ] Verdicts and execution states match their documented semantics.
- [ ] Failure examples cover insufficient/stale/tampered evidence, independence, handoff, and rollback.
- [ ] Migration notes identify v2 breaking changes.

## Public safety

- [ ] Examples use fictional identities, `example.org`, and documentation network ranges only.
- [ ] No credentials, secret-shaped environment values, private paths (POSIX or Windows), hosts, chat IDs, account IDs, or incident history appear.
- [ ] Working-tree, tracked-file, and Git-history sanitization modes pass.
- [ ] The pinned standard secret scanner passes.
- [ ] An independent reviewer checks the exact commit subject.

## Gates

- [ ] Python syntax compilation passes.
- [ ] Unit, CLI, semantic, and negative end-to-end tests pass.
- [ ] Editable package install plus `egmo --help`, `validate`, `judge`, and `create-task` smoke tests pass.
- [ ] Real Mermaid CLI rendering passes for standalone and inline diagrams.
- [ ] The malformed Mermaid fixture is rejected.
- [ ] Markdown lint and local link checks pass.
- [ ] `git diff --check` passes and the intended file list is reviewed.
- [ ] CI runs all corresponding gates with read-only repository permission.

## Release hygiene

- [ ] `LICENSE` and `README.md` are present and linked.
- [ ] Package/archive contents contain only publishable files.
- [ ] No release or visibility/history change is made without separate authorization.
