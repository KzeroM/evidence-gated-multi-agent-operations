# Publish Checklist

Use this before posting the package to a repository, gist, blog, or documentation site.

## Content

- [ ] README title and first paragraph are clear to a reader with no private context.
- [ ] Diagrams render correctly in the target platform.
- [ ] Examples use neutral role names and illustrative paths only.
- [ ] Output ownership principle is included.
- [ ] Good-vs-bad patterns are concrete and non-private.
- [ ] Mission contract examples are generic enough for public reuse.

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
- [ ] Archive/repository contains only publishable files.

## Final evidence

- [ ] Sanitization search returns zero matches for private terms.
- [ ] Markdown structural check passes.
- [ ] Archive contents were listed and reviewed.
