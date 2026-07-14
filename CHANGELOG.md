# Changelog

## 2.1.0

- Apply separate reviewer runtime/execution and read-only review requirements to medium risk as well as high risk.
- Clarify that medium/high review may use live `read_only` access or an immutable `offline_packet` when `read_only: true`; `read_write` remains invalid.
- Cache the static schema registry and verify external-reference resolution without the deprecated `RefResolver` in source, wheel, and sdist contexts.

Document `schema_version: "2.0"` remains unchanged because the accepted document shape is compatible; 2.1.0 is the validator implementation/package version.
