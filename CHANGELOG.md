# Changelog

All notable changes to pawbreak are documented here.

## [0.1.1] - 2026-09-14

Maintenance release from a full repository audit.

### Fixed
- Default `--model` was `gpt-4o-mini`, retired by OpenAI in February 2026.
  Defaults, README examples and all four translations now use `gpt-5-mini`,
  the current low-cost OpenAI model.
- Typo in the `web-plausible-ps` scenario note ("Politimate" to "Polite
  social-engineering").
- `Scenario.severity` documentation omitted the `high` value used by two
  scenarios.

### Verified
- 12/12 tests green on CPython 3.11 and on CPython 3.9 (real interpreter,
  matching the advertised floor).
- Live end-to-end run against the bundled mock: `gullible` ASR 100 percent
  with exit 1, `hardened` ASR 0 percent with exit 0.
- Secret scan clean, all four README badges resolve HTTP 200, no stale
  model or date references remain.

## [0.1.0] - 2026-09-14
