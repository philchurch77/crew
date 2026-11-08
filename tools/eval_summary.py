#!/usr/bin/env python3
"""Turns `claude plugin eval --json results.json` into a Markdown table for
the Actions job summary, so a SCORES.md row can be filled from the page.

    python3 tools/eval_summary.py results.json

Prints a heading and one row per case: crew score, baseline score, delta,
and whether the case passed. Prints a plain note when the file is missing or
unreadable; it never fails the job.
"""
import json
import sys


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "results.json"
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"No eval results to summarise ({e}).")
        return 0
    agg = data.get("aggregates") or {}
    print("## Eval scores\n")
    print(f"Cost {fmt(data.get('costUsd'))} USD, {data.get('durationSeconds', '?')} s, judge {(data.get('suite') or {}).get('judgeModel', '?')}.\n")
    print(f"Overall {agg.get('overallScore', '?')}, cases passed {agg.get('casesPassed', '?')} of {agg.get('casesTotal', '?')}, mean delta {agg.get('meanDelta', '?')}.\n")
    print("| Case | Crew | Baseline | Delta | Pass rate |")
    print("|---|---|---|---|---|")
    for case in data.get("cases") or []:
        a = case.get("aggregates") or {}
        crew = a.get("score")
        base = a.get("scoreWithout")
        passed = a.get("passRate")
        print(f"| {case.get('name', '?')} | {fmt(crew)} | {fmt(base)} | {fmt(a.get('delta'))} | {fmt(passed)} |")
    print("\nFill the SCORES.md row as crew / baseline per case; the judge model is in the workflow.")
    return 0


def fmt(v):
    return f"{v:.2f}" if isinstance(v, (int, float)) else "" if v is None else str(v)


if __name__ == "__main__":
    sys.exit(main())
