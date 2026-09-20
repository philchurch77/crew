#!/usr/bin/env python3
"""Holds every agent, command and skill to its word budget.

    python3 tools/budget.py            check every file, exit 1 on any overrun
    python3 tools/budget.py --table    print the table without failing

Budgets live in tools/budgets.json. The count is words, not lines, so a long
line cannot dodge it. A file over budget fails; a file under budget prints
its headroom. The rule for raising a budget is in AGENTS.md section 7: no
words are added unless an eval case fails without them, and the first move
is always to cut something instead.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUDGETS = os.path.join(ROOT, "tools", "budgets.json")


def words(path):
    with open(path, encoding="utf-8") as f:
        return len(f.read().split())


def main():
    table_only = "--table" in sys.argv
    with open(BUDGETS, encoding="utf-8") as f:
        budgets = {k: v for k, v in json.load(f).items() if not k.startswith("_")}

    over = []
    print(f"{'file':<48} {'words':>6} {'budget':>7} {'room':>6}")
    for rel, budget in sorted(budgets.items()):
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            print(f"{rel:<48} {'gone':>6} {budget:>7} {'':>6}  budgeted file is missing")
            over.append(rel)
            continue
        n = words(path)
        room = budget - n
        flag = "" if room >= 0 else "  OVER BUDGET"
        print(f"{rel:<48} {n:>6} {budget:>7} {room:>+6}{flag}")
        if room < 0:
            over.append(rel)

    unbudgeted = []
    for sub in ("plugins/crew/agents", "plugins/crew/commands", "plugins/crew/skills"):
        for dirpath, _, files in os.walk(os.path.join(ROOT, sub)):
            for name in files:
                if name.endswith(".md"):
                    rel = os.path.relpath(os.path.join(dirpath, name), ROOT)
                    if rel not in budgets and rel != "plugins/crew/commands/commit-message.md":
                        unbudgeted.append(rel)
    for rel in unbudgeted:
        print(f"{rel:<48} {words(os.path.join(ROOT, rel)):>6} {'none':>7} {'':>6}  no budget set")

    if table_only:
        return 0
    if over or unbudgeted:
        print()
        for rel in over:
            print(f"FAIL {rel} is over its word budget. Cut before you add; raise the budget only with a case that fails without the words.")
        for rel in unbudgeted:
            print(f"FAIL {rel} has no entry in tools/budgets.json.")
        return 1
    print("\nevery file is within budget")
    return 0


if __name__ == "__main__":
    sys.exit(main())
