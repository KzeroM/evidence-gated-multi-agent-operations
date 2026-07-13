# Contributing

Contributions should strengthen the evidence-gated pattern while keeping the repository vendor-neutral, reusable, and safe for public release.

## Contribution guidelines

- Use fictional organizations and `example.org` identities.
- Use documentation-only network ranges when an address is necessary.
- Do not include credentials, private identifiers, internal paths, task history, or operational topology.
- Preserve output ownership, explicit trust boundaries, and independent evidence review.
- Keep examples aligned with the JSON Schemas under `schemas/`.
- Do not change the CC BY 4.0 license without an explicit, documented licensing decision.

## Validation

Run the local checks before opening a pull request:

```bash
python3 -m pip install -r requirements-dev.txt
npm ci
npm run validate
npm test
npm run lint:markdown
npm run lint:mermaid
```

## Pull request checklist

- The change is useful and does not duplicate existing guidance or templates.
- New examples are fictional and public-safe.
- Durable outputs identify their owner, location, retention, and retrieval method.
- Tests cover new validation behavior.
- All local checks pass and remaining limitations are documented.
