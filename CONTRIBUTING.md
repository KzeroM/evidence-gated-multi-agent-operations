# Contributing

Contributions should strengthen the vendor-neutral evidence protocol without adding an agent runtime, scheduler, queue, browser worker, deployment engine, or provider-specific orchestration platform.

## Public-safe content

- Use fictional identities, `example.org`, and documentation IP ranges.
- Never add credentials, personal/private identifiers, internal hosts, private paths, chat IDs, incident history, or private topology.
- Every fenced YAML object must declare a supported `document_type` and `schema_version: "2.0"`.
- Keep standalone templates and Markdown examples aligned with strict schemas and cross-document rules.
- Preserve immutable subject binding, freshness, typed evidence, stable ID references, scoped capabilities, risk approval, and reviewer provenance.
- Breaking protocol changes require a new schema version and migration notes.

## Local gates

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m pip install -e .
PUPPETEER_SKIP_DOWNLOAD=true npm ci
python3 -m compileall -q egmo scripts tests
egmo validate --mode working-tree
egmo validate --mode tracked
egmo validate --mode history
python3 -m unittest discover -s tests -v
npm run smoke:package
npm run scan:secrets
npm run lint:markdown
npm run lint:mermaid
git diff --check
```

When using a system browser for Mermaid, set `PUPPETEER_EXECUTABLE_PATH` to its executable. CI downloads the pinned compatible renderer through the Mermaid CLI package.

## Pull request checklist

- Examples remain fictional and contain no task/private operational context.
- Schema, semantic, and end-to-end negative tests cover new behavior.
- Durable outputs name owner, location, retention, retrieval, and immutable subject.
- Risk and approval are proportional, and high-risk review is mechanically independent.
- All gates pass; any environmental blocker is described precisely.
- The CC BY 4.0 license is unchanged unless a separate explicit licensing decision exists.
