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

if [ "${1:-}" = "--with-django" ] && ! python3 -c "import django" >/dev/null 2>&1; then
  python3 -m venv .venv
  .venv/bin/pip install -q --disable-pip-version-check -r requirements.txt
fi
