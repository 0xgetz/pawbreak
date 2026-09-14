# Changelog

All notable changes to pawbreak are documented here.

## [0.1.0] - 2026-09-14

First public release.

### Added
- Red-team harness for tool-using agents: 10 scenarios across four surfaces
  (`file`, `web`, `email`, `tool_output`).
- Nine payload families: instruction override, fake system message,
  authority impersonation, roleplay escape, hidden text, tool-output
  poisoning, few-shot smuggling, encoded bait, plausible urgency.
- Tripwire sandbox with fake-success responses so breaches stay observable.
- Deterministic scoring: ASR, critical ASR, PAW-score, per-surface table.
- Bundled mock endpoint with `gullible` and `hardened` canned agents for
  offline demo and CI (loopback only).
- JSON + Markdown reports; CI-friendly exit codes (0 clean, 1 breach, 2 error).
- 12 offline tests; zero runtime dependencies (Python 3.9+ stdlib).
