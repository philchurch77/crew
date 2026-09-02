#!/usr/bin/env python3
"""PreToolUse guard for the Gunner.

Blocks git commands that rewrite the working tree. The Gunner breaks a line on
purpose to prove a test catches it, then puts it back; git checkout, restore,
stash, reset, clean and switch cannot tell that mutation from the developer's
own uncommitted work and would destroy both.

Reads the hook input on stdin. Acts only when the hook fires inside the gunner
subagent (agent_type "gunner" or "<plugin>:gunner"); every other caller is
allowed through untouched, as are the read-only `git stash list` and
`git stash show`. Exit code 2 blocks the tool call.
"""
import json
import re
import sys

BLOCKED = re.compile(
    r"\bgit\b(?:\s+-\S+(?:\s+\S+)?)*\s+(checkout|restore|reset|clean|switch|stash(?!\s+(?:list|show)\b))\b"
)


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0

    agent = str(data.get("agent_type") or "")
    if agent.split(":")[-1] != "gunner":
        return 0
    if data.get("tool_name") != "Bash":
        return 0

    command = str((data.get("tool_input") or {}).get("command") or "")
    match = BLOCKED.search(command)
    if not match:
        return 0

    reason = (
        f"Blocked: `git {match.group(1)}` is not allowed for the Gunner. It "
        "cannot tell your mutation from the developer's uncommitted work. "
        "Revert from the .bak copy you made before mutating, or stop and "
        "report if you have none."
    )
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )
    print(reason, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
