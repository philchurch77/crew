#!/usr/bin/env bash
# Seeds an eval workspace with the schoolapp fixture. Each case's scaffold.sh
# calls this; it runs in the empty workspace with cwd set there.
#
#   seed.sh                Copy the fixture and commit it.
#   seed.sh --with-django  Also make Django importable, for cases that run
#                          manage.py. Uses the system interpreter when it
#                          already has Django; otherwise builds .venv, which
#                          the fixture CLAUDE.md tells the crew to use.
#   seed.sh --with-django --demo
#                          Also migrate and run seed_demo, for cases whose
#                          symptom lives in the data rather than the code.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$HERE/schoolapp/." .
git init -q
git add -A
git -c user.name=fixture -c user.email=fixture@example.com commit -qm "Schoolapp fixture"

if [ "${1:-}" = "--with-django" ]; then
  # Pick an interpreter that already has Django. On Windows the `python3`
  # on Git Bash's PATH is often the Store stub, so try `python` too.
  PY=""
  for CAND in python3 python; do
    if "$CAND" -c "import django" >/dev/null 2>&1; then PY="$CAND"; break; fi
  done
  if [ -z "$PY" ]; then
    for CAND in python3 python; do
      if "$CAND" -c "import sys" >/dev/null 2>&1; then PY="$CAND"; break; fi
    done
    "$PY" -m venv .venv
    if [ -x .venv/bin/pip ]; then PIP=.venv/bin/pip; PY=.venv/bin/python; else PIP=.venv/Scripts/pip.exe; PY=.venv/Scripts/python.exe; fi
    "$PIP" install -q --disable-pip-version-check --timeout 60 --retries 5 -r requirements.txt
  fi
  if [ "${2:-}" = "--demo" ]; then
    "$PY" manage.py migrate -v0
    "$PY" manage.py seed_demo
  fi
fi
