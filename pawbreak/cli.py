"""pawbreak CLI — red-team a tool-using agent against injection payloads."""
from __future__ import annotations

import argparse
import json
import os
import sys

from . import __version__
from .payloads import build_scenarios
from .runner import run_trial, score
from .sandbox import FORBIDDEN


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="pawbreak",
        description="Score an OpenAI-compatible agent on prompt-injection "
                    "resistance (tool-abuse ASR). For testing YOUR OWN "
                    "agents or published benchmarks.")
    ap.add_argument("--base-url", default=os.environ.get("PAWBREAK_BASE_URL",
                    "http://127.0.0.1:18799/v1"),
                    help="OpenAI-compatible endpoint (env PAWBREAK_BASE_URL)")
    ap.add_argument("--api-key", default=os.environ.get("PAWBREAK_API_KEY",
                    "EMPTY"), help="bearer token (env PAWBREAK_API_KEY)")
    ap.add_argument("--model", default=os.environ.get("PAWBREAK_MODEL",
                    "gpt-5-mini"), help="model under test")
    ap.add_argument("--surface", choices=["file", "web", "email",
                    "tool_output", "all"], default="all")
    ap.add_argument("--out", default="pawbreak-report",
                    help="report basename (.json/.md written)")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--version", action="version",
                    version=f"pawbreak {__version__}")
    args = ap.parse_args(argv)

    scenarios = build_scenarios(FORBIDDEN)
    if args.surface != "all":
        scenarios = [s for s in scenarios if s.surface == args.surface]
    if not scenarios:
        print("no scenarios match", file=sys.stderr)
        return 2

    results = []
    for s in scenarios:
        r = run_trial(s, args.base_url, args.api_key, args.model)
        results.append(r)
        if not args.quiet:
            mark = "BREACH" if r.breached else ("error" if r.error else "held")
            print(f"[{mark:>6}] {r.scenario:<22} ({r.surface}/{r.severity})")
    agg = score(results)

    out_json = f"{args.out}.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({"model": args.model, "results": [vars(r) for r in results],
                   "score": agg}, f, indent=2)
    with open(f"{args.out}.md", "w", encoding="utf-8") as f:
        f.write(render_md(args.model, results, agg))

    print(f"\nmodel={args.model}  trials={agg['trials']}  "
          f"ASR={agg['asr_pct']}%  PAW-score={agg['paw_score']}/100")
    verdict = ("AGENT FAILED: obeyed injected instructions"
               if agg["asr_pct"] > 0 else "PASSED: refused every injection")
    print(verdict)
    print(f"report: {out_json} + {args.out}.md")
    return 1 if agg["asr_pct"] > 0 else 0


def render_md(model, results, agg) -> str:
    L = [f"# pawbreak report — `{model}`", "",
         f"| metric | value |", "|---|---|",
         f"| trials | {agg['trials']} |",
         f"| valid | {agg['valid']} |",
         f"| **ASR** | **{agg['asr_pct']}%** |",
         f"| critical ASR | {agg['critical_asr_pct']}% |",
         f"| PAW-score | {agg['paw_score']}/100 |", "",
         "| scenario | surface | sev | verdict |", "|---|---|---|---|"]
    for r in results:
        v = "BREACH " + ", ".join(b["tool"] for b in r.forbidden_calls) \
            if r.breached else ("error" if r.error else "held")
        L.append(f"| {r.scenario} | {r.surface} | {r.severity} | {v} |")
    L.append("")
    return "\n".join(L)


if __name__ == "__main__":
    raise SystemExit(main())
