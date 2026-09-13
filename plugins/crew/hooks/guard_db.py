#!/usr/bin/env python3
"""PreToolUse guard for the crew's read-only agents.

Every agent but the Gunner audits and reports; none of them changes the
developer's database. Their definitions say so, and this makes it so. Blocks
management commands that write to the database when the hook fires inside one
of those agents. showmigrations, sqlmigrate, makemigrations --check --dry-run,
migrate --check and migrate --plan stay allowed: they read.

Reads the hook input on stdin. Exit code 2 blocks the tool call.
"""
import json
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

WRITES = re.compile(
    r"\b(?:manage\.py|django-admin(?:\.py)?)\s+(?:-{1,2}[\w-]+(?:[= ]\S+)?\s+)*"
    r"(migrate|flush|loaddata|dbshell|createsuperuser|changepassword|sqlsequencereset)\b"
)
FAKE = re.compile(r"\b(?:manage\.py|django-admin(?:\.py)?)\b[^\n;&|]*--fake")
READ_ONLY_MIGRATE = re.compile(r"\bmigrate\b[^\n;&|]*--(check|plan)\b")
DELETE_DB = re.compile(r"\b(?:rm|del|Remove-Item)\b[^\n;&|]*\.(?:sqlite3?|db)\b")


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0

    agent = str(data.get("agent_type") or "").split(":")[-1]
    if agent not in READ_ONLY_AGENTS:
        return 0
    if data.get("tool_name") != "Bash":
        return 0

    command = str((data.get("tool_input") or {}).get("command") or "")
    what = None
    match = WRITES.search(command)
    if match:
        what = f"manage.py {match.group(1)}"
        if match.group(1) == "migrate" and READ_ONLY_MIGRATE.search(command):
            what = None
    if what is None and FAKE.search(command):
        what = "--fake"
    if what is None and DELETE_DB.search(command):
        what = "deleting the database file"
    if what is None:
        return 0

    reason = (
        f"[crew hook: guard_db] Blocked: `{what}` changes the developer's database, and the "
        f"{agent} audits and reports without changing anything. Read-only "
        "commands are fine: showmigrations, sqlmigrate, makemigrations "
        "--check --dry-run, migrate --check, migrate --plan. If the task "
        "genuinely needs this command, stop and say so in your report."
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
