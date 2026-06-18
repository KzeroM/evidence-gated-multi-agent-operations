# Publish Checklist

Use this before posting the package to a repository, gist, blog, or documentation site.

## Content

- [ ] README title and first paragraph are clear to a reader with no private context.
- [ ] Diagrams render correctly in the target platform.
- [ ] Examples use neutral role names and illustrative paths only.
- [ ] Output ownership principle is included.
- [ ] Good-vs-bad patterns are concrete and non-private.
- [ ] Mission contract examples are generic enough for public reuse.
- [ ] `THREAT_MODEL.md` covers prompt injection, untrusted tool output, artifact tampering, secret leakage, audit integrity, and reviewer independence.

## Sanitization

- [ ] No private agent names or operating names.
- [ ] No personal chat IDs, account IDs, usernames, machine names, or private paths.
- [ ] No webhook URLs, tokens, cookies, API keys, or secret names.
- [ ] No exact private relay topology, firewall assumptions, or sensitive port mapping.
- [ ] No provider-specific billing/auth details unless intentionally documented.

## Packaging

- [ ] License chosen and committed.
- [ ] `LICENSE_OPTIONS.md` replaced or supplemented by a real license.
- [ ] `README.md` is the entry point.
- [ ] `diagrams/` files match the inline Mermaid diagrams.
- [ ] `schemas/` and `examples/` validate locally or in CI.
- [ ] `.github/workflows/validate.yml` runs validation, Markdown lint, link check, Mermaid render, and sanitization scan.
- [ ] Archive/repository contains only publishable files.

## Final evidence

- [ ] Sanitization search returns zero matches for private terms.
- [ ] Schema/example validation passes.
- [ ] Markdown structural check passes.
- [ ] Link check passes or known external failures are documented.
- [ ] Mermaid diagrams render.
- [ ] Archive contents were listed and reviewed.
