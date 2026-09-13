#!/usr/bin/env python3
"""Stop hook: the two checks the Articles say happen before work is called
finished, run whether or not anyone remembered.

1. Article 6: if a models.py has changed this session, `makemigrations
   --check --dry-run` must report nothing. A model change with no migration
   is work that is not finished, and the migration it needs is what the
   Purser reads.
2. Article 7: no changed template carries a `{# #}`, `{{ }}` or `{% %}`
   split across lines.

Runs in the main session only, once per turn: when Claude Code is already
continuing because of a stop hook (`stop_hook_active`) it allows, so the
developer is never trapped. Anything the check cannot establish (no git, no
Django, no manage.py, a timeout) allows too.
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import template_leaks  # noqa: E402

MODELS = re.compile(r"(^|/)models\.py$|(^|/)models/[^/]+\.py$")
TEMPLATE = re.compile(r"\.(html|htm|djhtml)$")


def changed_files(cwd):
    out = subprocess.run(["git", "-C", cwd, "status", "--porcelain", "-z"], capture_output=True, timeout=20)
    if out.returncode != 0:
        return None
    files = []
    for entry in out.stdout.decode("utf-8", "replace").split("\0"):
        if len(entry) > 3:
            files.append(entry[3:].replace("\\", "/"))
    return files


def find_manage(cwd):
    direct = os.path.join(cwd, "manage.py")
    if os.path.exists(direct):
        return cwd
    found = []
    try:
        for name in os.listdir(cwd):
            if os.path.exists(os.path.join(cwd, name, "manage.py")):
                found.append(os.path.join(cwd, name))
    except OSError:
        return None
    return found[0] if len(found) == 1 else None


def find_python(project):
    candidates = []
    for venv in (".venv", "venv", "env"):
        candidates.append(os.path.join(project, venv, "bin", "python"))
        candidates.append(os.path.join(project, venv, "Scripts", "python.exe"))
    if os.environ.get("VIRTUAL_ENV"):
        candidates.append(os.path.join(os.environ["VIRTUAL_ENV"], "bin", "python"))
        candidates.append(os.path.join(os.environ["VIRTUAL_ENV"], "Scripts", "python.exe"))
    candidates += ["python", "python3", sys.executable]
    for py in candidates:
        if os.sep in py and not os.path.exists(py):
            continue
        try:
            ok = subprocess.run([py, "-c", "import django"], capture_output=True, timeout=30)
        except Exception:
            continue
        if ok.returncode == 0:
            return py
    return None


def missing_migrations(project):
    py = find_python(project)
    if py is None:
        return None
    try:
        out = subprocess.run(
            [py, "manage.py", "makemigrations", "--check", "--dry-run"],
            cwd=project,
            capture_output=True,
            timeout=90,
        )
    except Exception:
        return None
    text = (out.stdout + out.stderr).decode("utf-8", "replace")
    if out.returncode != 0 and "Migrations for" in text:
        return text.strip()
    return None


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    if data.get("agent_id") or data.get("stop_hook_active"):
        return 0
    cwd = data.get("cwd") or os.getcwd()
    try:
        files = changed_files(cwd)
    except Exception:
        return 0
    if not files:
        return 0

    reasons = []
    if any(MODELS.search(f) for f in files):
        project = find_manage(cwd)
        if project:
            text = missing_migrations(project)
            if text:
                reasons.append(
                    "A models.py changed this session and `makemigrations --check --dry-run` reports a migration "
                    "that has not been made (article 6). Make it, read it before running it, and if it removes, "
                    "renames, retypes or shrinks a column, the Purser reads it before the work is called done.\n"
                    + text[:1500]
                )
    for f in files:
        if TEMPLATE.search(f):
            path = os.path.join(cwd, f)
            if os.path.isfile(path):
                leaks, _ = template_leaks.scan(path)
                if leaks:
                    reasons.append(template_leaks.report(f, leaks, []))
    if not reasons:
        return 0
    print(json.dumps({"decision": "block", "reason": "\n\n".join(reasons)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
