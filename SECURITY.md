# Security Policy

## Scope

This repository is a public reference package. Its supported release is the latest commit on the default branch. It should contain only reusable guidance, fictional examples, deterministic validation, and public-safe metadata.

## Reporting a vulnerability

Use the repository's private vulnerability-reporting feature when it is available. If it is unavailable, open a minimal public issue that requests a private maintainer contact without including sensitive details.

Never put credentials, private operational details, personal data, private repository identifiers, internal hostnames, chat identifiers, or non-public evidence in a public issue.

## If sensitive material is found

1. Stop distributing the affected copy.
2. Preserve only the minimum evidence needed for a private investigation.
3. Remove the material from the current tree and assess whether history is affected.
4. Rotate any exposed credential through its owning system.
5. Re-run the repository validation and perform an independent public-safety review before publishing again.

The validation scripts are defense in depth. A passing scan cannot prove that every sensitive value has been omitted.
