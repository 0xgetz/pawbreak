# Contributing to pawbreak

Thanks for helping make agents harder to fool.

## Ground rules

1. **Zero runtime dependencies.** Python stdlib only.
2. **Payloads stay inert.** A payload may only reference the sandbox
   tripwire tools (`wipe_workspace`, `send_report`, `show_secrets`). No
   real-world attack instructions, no malware, no targeting material.
3. **Every scenario is reproducible.** Temperature 0, deterministic mock
   agents, no network calls in the test suite.
4. **Score first.** If you change scoring math, run both mock agents:
   `hardened` must score 100 and `gullible` must fail. If either invariant
   breaks, the harness is lying to users.

## Adding a scenario

1. Add a `Scenario(...)` in `pawbreak/payloads.py` with a unique id.
2. Add one assertion in `test/test_pawbreak.py`.
3. Run `python3 -m unittest discover -s test` fully offline.
4. PRs: show the before/after ASR table for the two mock agents.

## Reporting a new injection family

Open an issue with the technique name, the artifact surface it abuses, and
a synthetic example payload (not a live campaign). We will review for the
corpus; real campaign text is out of scope.

## Style

- Keep the report format stable; downstream CI parses it.
- Docs: README exists in five languages. Translate any user-facing change
  in the same PR or note `translation-needed` in the description.

MIT-licensed. By contributing you agree your work ships under MIT.
