#!/usr/bin/env python3
"""Feeds each hook the inputs it must act on and the ones it must let through.

    python3 plugins/crew/hooks/selftest.py

Run it after any change to a hook. It needs git; the before_stop migration
check also needs a Python with Django on PATH and is skipped otherwise.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FAILS = []


def run(script, payload, *args, cwd=None):
    p = subprocess.run(
        [sys.executable, os.path.join(HERE, script), *args],
        input=json.dumps(payload).encode(),
        capture_output=True,
        cwd=cwd,
    )
    out = {}
    if p.stdout.strip():
        try:
            out = json.loads(p.stdout.decode())
        except ValueError:
            out = {"raw": p.stdout.decode()}
    return p.returncode, out


def check(name, cond, detail=""):
    print(("ok   " if cond else "FAIL ") + name + (f"  {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


def bash(agent, command):
    return {"agent_type": agent, "tool_name": "Bash", "tool_input": {"command": command}}


# guard-git ------------------------------------------------------------------
code, _ = run("guard-git.py", bash("gunner", "git stash"))
check("guard-git blocks gunner git stash", code == 2)
code, _ = run("guard-git.py", bash("crew:gunner", "git checkout -- app/views.py"))
check("guard-git blocks plugin-scoped gunner checkout", code == 2)
code, _ = run("guard-git.py", bash("gunner", "git stash list"))
check("guard-git allows git stash list", code == 0)
code, _ = run("guard-git.py", bash("purser", "git stash"))
check("guard-git ignores other agents", code == 0)

# guard_db -------------------------------------------------------------------
for agent in ("purser", "crew:surgeon", "lookout", "master-at-arms"):
    code, _ = run("guard_db.py", bash(agent, "python manage.py migrate"))
    check(f"guard_db blocks {agent} migrate", code == 2)
code, _ = run("guard_db.py", bash("purser", ".venv/bin/python manage.py migrate --fake tolerance 0001"))
check("guard_db blocks --fake", code == 2)
code, _ = run("guard_db.py", bash("lookout", "python manage.py flush --noinput"))
check("guard_db blocks flush", code == 2)
code, _ = run("guard_db.py", bash("lookout", "python manage.py loaddata seed.json"))
check("guard_db blocks loaddata", code == 2)
code, _ = run("guard_db.py", bash("surgeon", "rm db.sqlite3"))
check("guard_db blocks deleting the sqlite file", code == 2)
for cmd in (
    "python manage.py showmigrations",
    "python manage.py sqlmigrate tolerance 0002",
    "python manage.py makemigrations --check --dry-run",
    "python manage.py migrate --check",
    "python manage.py migrate --plan",
    "python manage.py shell < /tmp/walk.py",
    "python manage.py runserver 8001",
    "python manage.py test tolerance",
):
    code, _ = run("guard_db.py", bash("purser", cmd))
    check(f"guard_db allows {cmd.split('manage.py ')[1]}", code == 0)
code, _ = run("guard_db.py", bash("gunner", "python manage.py migrate"))
check("guard_db ignores the gunner", code == 0)
code, _ = run("guard_db.py", bash("", "python manage.py migrate"))
check("guard_db ignores the main session", code == 0)

# guard_edit -----------------------------------------------------------------
def write(agent, path, tool="Write"):
    return {"agent_type": agent, "tool_name": tool, "tool_input": {"file_path": path}}

code, _ = run("guard_edit.py", write("crew:purser", "/proj/tolerance/views.py"))
check("guard_edit blocks purser writing views.py", code == 2)
code, _ = run("guard_edit.py", write("carpenter", "/proj/app/views.py", "Edit"))
check("guard_edit blocks carpenter editing views.py", code == 2)
code, _ = run("guard_edit.py", write("master-at-arms", "/proj/.claude/agent-memory/master-at-arms/MEMORY.md"))
check("guard_edit allows writing to project memory", code == 0)
code, _ = run("guard_edit.py", write("quartermaster", "C:\\Users\\me\\.claude\\agent-memory\\quartermaster\\notes.md", "Edit"))
check("guard_edit allows user memory on Windows paths", code == 0)
code, _ = run("guard_edit.py", write("purser", "/proj/.claude/agent-memory-local/purser/MEMORY.md"))
check("guard_edit allows local memory", code == 0)
code, _ = run("guard_edit.py", write("gunner", "/proj/tolerance/tests.py"))
check("guard_edit ignores the gunner", code == 0)
code, _ = run("guard_edit.py", write("", "/proj/tolerance/views.py"))
check("guard_edit ignores the main session", code == 0)
code, _ = run("guard_edit.py", {"agent_type": "purser", "tool_name": "Read", "tool_input": {"file_path": "/proj/x.py"}})
check("guard_edit ignores Read", code == 0)

# guard_tree -----------------------------------------------------------------
tmp = tempfile.mkdtemp(prefix="crew-selftest-")
try:
    subprocess.run(["git", "init", "-q", tmp], check=True)
    os.makedirs(os.path.join(tmp, "app"))
    with open(os.path.join(tmp, "app", "views.py"), "w") as f:
        f.write("def view():\n    return 1\n")
    with open(os.path.join(tmp, "app", "tests.py"), "w") as f:
        f.write("")
    with open(os.path.join(tmp, "notes.md"), "w") as f:
        f.write("developer's uncommitted note\n")
    subprocess.run(["git", "-C", tmp, "add", "-A"], check=True)
    subprocess.run(["git", "-C", tmp, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "init"], check=True)

    def agent(kind, aid):
        return {"session_id": "selftest", "agent_id": aid, "agent_type": kind, "cwd": tmp}

    # gunner: tests changed, views.py mutated and restored, no .bak
    run("guard_tree.py", agent("crew:gunner", "g1"), "snapshot")
    with open(os.path.join(tmp, "app", "tests.py"), "w") as f:
        f.write("class T: pass\n")
    shutil.copy(os.path.join(tmp, "app", "views.py"), os.path.join(tmp, "app", "views.py.bak"))
    with open(os.path.join(tmp, "app", "views.py"), "a") as f:
        f.write("# mutated\n")
    code, out = run("guard_tree.py", agent("crew:gunner", "g1"), "check")
    check("guard_tree blocks gunner with mutated views.py and .bak", out.get("decision") == "block", str(out))
    check("guard_tree names views.py", "app/views.py (changed)" in out.get("reason", ""))
    check("guard_tree names the .bak", "views.py.bak" in out.get("reason", ""))
    shutil.move(os.path.join(tmp, "app", "views.py.bak"), os.path.join(tmp, "app", "views.py"))
    code, out = run("guard_tree.py", agent("crew:gunner", "g1"), "check")
    check("guard_tree allows gunner once restored, tests changed", out.get("decision") is None, str(out))
    os.makedirs(os.path.join(tmp, "app", "tests"))
    run("guard_tree.py", agent("gunner", "g2"), "snapshot")
    with open(os.path.join(tmp, "app", "tests", "test_perms.py"), "w") as f:
        f.write("x = 1\n")
    code, out = run("guard_tree.py", agent("gunner", "g2"), "check")
    check("guard_tree allows new file under tests/", out.get("decision") is None, str(out))

    # gunner: cannot restore, gives up after MAX_BLOCKS
    run("guard_tree.py", agent("gunner", "g3"), "snapshot")
    with open(os.path.join(tmp, "app", "views.py"), "a") as f:
        f.write("# stuck\n")
    blocks = sum(1 for _ in range(4) if run("guard_tree.py", agent("gunner", "g3"), "check")[1].get("decision") == "block")
    check("guard_tree stops blocking after two refusals", blocks == 2, f"blocked {blocks}x")
    subprocess.run(["git", "-C", tmp, "checkout", "--", "app/views.py"], check=True)

    # lookout: any change blocks; sqlite and pycache do not
    run("guard_tree.py", agent("crew:lookout", "l1"), "snapshot")
    with open(os.path.join(tmp, "db.sqlite3"), "wb") as f:
        f.write(b"x")
    os.makedirs(os.path.join(tmp, "app", "__pycache__"))
    with open(os.path.join(tmp, "app", "__pycache__", "views.cpython-311.pyc"), "wb") as f:
        f.write(b"x")
    code, out = run("guard_tree.py", agent("crew:lookout", "l1"), "check")
    check("guard_tree ignores sqlite and pycache for lookout", out.get("decision") is None, str(out))
    run("guard_tree.py", agent("crew:lookout", "l2"), "snapshot")
    with open(os.path.join(tmp, "walk.py"), "w") as f:
        f.write("print(1)\n")
    code, out = run("guard_tree.py", agent("crew:lookout", "l2"), "check")
    check("guard_tree blocks lookout leaving walk.py", out.get("decision") == "block" and "walk.py (new)" in out.get("reason", ""), str(out))
    os.remove(os.path.join(tmp, "walk.py"))
    code, out = run("guard_tree.py", agent("crew:lookout", "l2"), "check")
    check("guard_tree allows lookout once walk.py is gone", out.get("decision") is None, str(out))

    # other agents untouched
    run("guard_tree.py", agent("purser", "p1"), "snapshot")
    with open(os.path.join(tmp, "notes.md"), "a") as f:
        f.write("more\n")
    code, out = run("guard_tree.py", agent("purser", "p1"), "check")
    check("guard_tree ignores the purser", out == {} and code == 0)
finally:
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.rmtree(os.path.join(tempfile.gettempdir(), "crew-hooks", "selftest"), ignore_errors=True)

# template_leaks -------------------------------------------------------------
tmp = tempfile.mkdtemp(prefix="crew-selftest-")
try:
    bad = os.path.join(tmp, "bad.html")
    with open(bad, "w") as f:
        f.write("{% extends 'base.html' %}\n{# one line is fine #}\n{# split across\n   two lines #}\n<p>{{ x }}</p>\n{% if a\n%}x{% endif %}\n<!-- dev note -->\n")
    good = os.path.join(tmp, "good.html")
    with open(good, "w") as f:
        f.write("{% extends 'base.html' %}\n{# fine #}\n{% comment %}\nlong note\n{% endcomment %}\n<p>{{ x }} {% if a %}b{% endif %}</p>\n")

    def edit(path):
        return {"tool_name": "Edit", "tool_input": {"file_path": path}}

    code, out = run("template_leaks.py", edit(bad))
    reason = out.get("reason", "")
    check("template_leaks blocks the split comment", out.get("decision") == "block", str(out))
    check("template_leaks reports lines 3, 4, 6 and 7", all(f"line {n}:" in reason for n in (3, 4, 6, 7)) and "line 2:" not in reason and "line 5:" not in reason, reason)
    check("template_leaks mentions the HTML comment", "HTML comment" in reason)
    code, out = run("template_leaks.py", edit(good))
    check("template_leaks allows a clean template", out == {} and code == 0, str(out))
    code, out = run("template_leaks.py", edit(os.path.join(tmp, "views.py")))
    check("template_leaks ignores non-templates", out == {} and code == 0)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# before_stop ----------------------------------------------------------------
fixture = os.path.join(HERE, "..", "evals", "_fixture", "schoolapp")
tmp = tempfile.mkdtemp(prefix="crew-selftest-")
try:
    shutil.copytree(fixture, tmp, dirs_exist_ok=True)
    subprocess.run(["git", "init", "-q", tmp], check=True)
    subprocess.run(["git", "-C", tmp, "add", "-A"], check=True)
    subprocess.run(["git", "-C", tmp, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "init"], check=True)
    stop = {"session_id": "selftest", "cwd": tmp, "stop_hook_active": False}

    code, out = run("before_stop.py", stop)
    check("before_stop allows a clean tree", out == {} and code == 0, str(out))

    tpl = os.path.join(tmp, "tolerance", "templates", "tolerance", "observation_form.html")
    with open(tpl, "a") as f:
        f.write("{# split\n comment #}\n")
    code, out = run("before_stop.py", stop)
    check("before_stop blocks on a changed template that leaks", out.get("decision") == "block" and "observation_form.html" in out.get("reason", ""), str(out))
    code, out = run("before_stop.py", dict(stop, stop_hook_active=True))
    check("before_stop allows when already continuing", out == {})
    code, out = run("before_stop.py", dict(stop, agent_id="x"))
    check("before_stop ignores subagents", out == {})
    subprocess.run(["git", "-C", tmp, "checkout", "--", "."], check=True)

    has_django = subprocess.run([sys.executable, "-c", "import django"], capture_output=True).returncode == 0
    if has_django:
        models = os.path.join(tmp, "tolerance", "models.py")
        with open(models, "a") as f:
            f.write("\n    note = models.TextField(blank=True)\n")
        code, out = run("before_stop.py", stop)
        check("before_stop blocks on a model change with no migration", out.get("decision") == "block" and "Migrations for" in out.get("reason", ""), str(out)[:300])
    else:
        print("skip before_stop migration check: run this with a Python that has Django, e.g. .venv/bin/python selftest.py")
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print()
if FAILS:
    print(f"{len(FAILS)} failed: " + ", ".join(FAILS))
    sys.exit(1)
print("all hooks behave")
