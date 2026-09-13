#!/usr/bin/env python3
"""PreToolUse guard: the reviewers write to their memory and nowhere else.

Every agent but the Gunner reports without editing. Giving an agent a
`memory` directory switches on Write and Edit for it, so this confines those
tools: inside one of the read-only agents, a Write, Edit, MultiEdit or
NotebookEdit is allowed only when the path is under an agent-memory
directory. Everything else is refused with the reason.

Reads the hook input on stdin. Exit code 2 blocks the tool call.
"""
import json
import os
import re
import sys

READ_ONLY_AGENTS = {
    "quartermaster",
    "carpenter",
    "surgeon",
    "bosun",
    "lookout",
    "master-at-arms",
    "purser",
}
EDIT_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
MEMORY_DIR = re.compile(r"(^|/)\.claude/agent-memory(-local)?/")


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0

    agent = str(data.get("agent_type") or "").split(":")[-1]
    if agent not in READ_ONLY_AGENTS:
        return 0
    if data.get("tool_name") not in EDIT_TOOLS:
        return 0

    tool_input = data.get("tool_input") or {}
    path = str(tool_input.get("file_path") or tool_input.get("notebook_path") or "")
    if MEMORY_DIR.search(path.replace("\\", "/")):
        return 0

    reason = (
        f"[crew hook: guard_edit] Blocked: the {agent} audits and reports; it does not edit files. "
        f"`{os.path.basename(path) or 'that file'}` is outside your memory directory, which is the only place "
        "you write. Put the change in your report for the Captain to make."
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
