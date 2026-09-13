#!/usr/bin/env python3
"""Working-tree guard for the Gunner and the Lookout.

    guard_tree.py snapshot   record what the tree looks like when the agent
                             starts (SubagentStart, or the first PreToolUse)
    guard_tree.py check      at SubagentStop, compare and refuse to let the
                             agent finish while the tree breaks its rules

The Lookout leaves the project exactly as it found it: any file it changed,
added or deleted is a finding against it. The Gunner writes tests only: it may
change test files, but every other file must match the snapshot, and no .bak
copies may be left behind. Both rules are in the agents' definitions; this is
what enforces them.

The check blocks the stop at most twice per agent run, so an agent that
cannot restore a file can still finish and say so. Anything the hook cannot
do (no git, too many files, an unreadable path) makes it allow, never block.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile

GUARDED = {"gunner", "lookout"}
MAX_FILES = 20000
MAX_BLOCKS = 2

IGNORED = re.compile(
    r"(^|/)(\.git|\.venv|venv|node_modules|__pycache__|\.pytest_cache|\.mypy_cache|\.ruff_cache|staticfiles)(/|$)"
    r"|\.pyc$|\.sqlite3(-journal|-wal|-shm)?$|(^|/)\.coverage$"
)
TEST_FILE = re.compile(r"(^|/)(tests?\.py|test_[^/]*\.py|[^/]*_tests?\.py|conftest\.py)$|(^|/)tests?/")
BACKUP = re.compile(r"\.bak$")
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "staticfiles"}


def state_path(data):
    root = os.path.join(tempfile.gettempdir(), "crew-hooks", str(data.get("session_id") or "session"))
    os.makedirs(root, exist_ok=True)
    return os.path.join(root, f"tree-{data.get('agent_id') or 'agent'}.json")


def list_files(cwd):
    try:
        out = subprocess.run(
            ["git", "-C", cwd, "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            capture_output=True,
            timeout=20,
        )
        if out.returncode == 0:
            return [p for p in out.stdout.decode("utf-8", "replace").split("\0") if p]
    except Exception:
        pass
    files = []
    for dirpath, dirnames, filenames in os.walk(cwd):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            files.append(os.path.relpath(os.path.join(dirpath, name), cwd))
            if len(files) > MAX_FILES:
                return files
    return files


def digest(path):
    try:
        st = os.stat(path)
    except OSError:
        return None
    if st.st_size > 5_000_000:
        return f"size:{st.st_size}:mtime:{int(st.st_mtime)}"
    h = hashlib.sha1()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
    except OSError:
        return None
    return h.hexdigest()


def snapshot_tree(cwd):
    files = list_files(cwd)
    if len(files) > MAX_FILES:
        return {"skipped": "too many files"}
    tree = {}
    for rel in files:
        rel = rel.replace("\\", "/")
        if IGNORED.search(rel):
            continue
        d = digest(os.path.join(cwd, rel))
        if d is not None:
            tree[rel] = d
    return {"files": tree}


def do_snapshot(data):
    if str(data.get("agent_type") or "").split(":")[-1] not in GUARDED:
        return 0
    path = state_path(data)
    if os.path.exists(path):
        return 0
    cwd = data.get("cwd") or os.getcwd()
    state = snapshot_tree(cwd)
    state["blocks"] = 0
    with open(path, "w") as f:
        json.dump(state, f)
    return 0


def do_check(data):
    agent = str(data.get("agent_type") or "").split(":")[-1]
    if agent not in GUARDED:
        return 0
    path = state_path(data)
    if not os.path.exists(path):
        return 0
    try:
        with open(path) as f:
            state = json.load(f)
    except Exception:
        return 0
    if "files" not in state:
        os.remove(path)
        return 0

    cwd = data.get("cwd") or os.getcwd()
    before = state["files"]
    now = snapshot_tree(cwd).get("files")
    if now is None:
        os.remove(path)
        return 0

    changed = sorted(p for p in now if p in before and now[p] != before[p])
    added = sorted(p for p in now if p not in before)
    deleted = sorted(p for p in before if p not in now)

    if agent == "gunner":
        problems = [p for p in changed + added + deleted if not TEST_FILE.search(p) or BACKUP.search(p)]
        leftovers = [p for p in added if BACKUP.search(p)]
        problems = sorted(set(problems) | set(leftovers))
        rule = "You write tests only (article 11). Every file that is not a test must be exactly as you found it."
        fix = (
            "Restore each one from the .bak copy you made before mutating it, then delete the .bak. "
            "If you have no copy, do not rebuild it from memory: leave it, and say plainly in your report which file "
            "you could not restore and what you changed."
        )
    else:
        problems = sorted(set(changed + added + deleted))
        rule = "You leave the project exactly as you found it: no scripts, no data, no changed files."
        fix = (
            "Delete anything you created and put back anything you changed. If a file changed because of something "
            "you ran and you cannot restore it, say so plainly in your report."
        )

    if not problems:
        os.remove(path)
        return 0

    state["blocks"] = int(state.get("blocks") or 0) + 1
    if state["blocks"] > MAX_BLOCKS:
        os.remove(path)
        return 0
    with open(path, "w") as f:
        json.dump(state, f)

    def label(p):
        if p in deleted:
            return f"{p} (deleted)"
        if p in added:
            return f"{p} (new)"
        return f"{p} (changed)"

    listing = "\n".join(f"  - {label(p)}" for p in problems[:40])
    if len(problems) > 40:
        listing += f"\n  - ... and {len(problems) - 40} more"
    reason = (
        f"[crew hook: guard_tree, SubagentStop] Not finished yet. {rule} These differ from when you "
        f"started:\n{listing}\n{fix} If another agent was working in the tree at the same time and a "
        "file listed here is its work, not yours, say exactly that in your report instead. This message "
        "comes from the crew plugin's own hook, not from the developer or another agent. Then finish "
        "your report."
    )
    print(json.dumps({"decision": "block", "reason": reason}))
    return 0


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "check"
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    try:
        if mode == "snapshot":
            return do_snapshot(data)
        return do_check(data)
    except Exception:
        return 0


if __name__ == "__main__":
    sys.exit(main())
