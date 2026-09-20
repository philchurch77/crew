#!/usr/bin/env bash
# Seeds an eval workspace with the schoolapp fixture. Each case's scaffold.sh
# calls this; it runs in the empty workspace with cwd set there.
#
#   seed.sh                Copy the fixture and commit it.
#   seed.sh --with-django  Also make Django importable, for cases that run
#                          manage.py. Uses the system interpreter when it
#                          already has Django; otherwise builds .venv, which
#                          the fixture CLAUDE.md tells the crew to use.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$HERE/schoolapp/." .
git init -q
git add -A
git -c user.name=fixture -c user.email=fixture@example.com commit -qm "Schoolapp fixture"

if [ "${1:-}" = "--with-django" ]; then
  # Pick an interpreter that already has Django. On Windows the `python3`
  # on Git Bash's PATH is often the Store stub, so try `python` too.
  for PY in python3 python; do
    if "$PY" -c "import django" >/dev/null 2>&1; then exit 0; fi
  done
  for PY in python3 python; do
    if "$PY" -c "import sys" >/dev/null 2>&1; then break; fi
  done
  "$PY" -m venv .venv
  if [ -x .venv/bin/pip ]; then PIP=.venv/bin/pip; else PIP=.venv/Scripts/pip.exe; fi
  "$PIP" install -q --disable-pip-version-check --timeout 60 --retries 5 -r requirements.txt
fi
