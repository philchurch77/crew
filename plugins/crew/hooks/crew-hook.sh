#!/bin/sh
# Runs one of the crew's hook scripts: `crew-hook.sh <name> [args]` runs
# hooks/<name>.py with whichever Python is on PATH and passes stdin through.
#
# hooks.json (plugin route) and the agents' frontmatter (junction route) both
# call this, so the Python lookup lives in one place. If there is no Python,
# a guard script fails closed (exit 2, the tool call is refused) and a check
# script fails open (exit 0) so a missing interpreter can never block the
# main session from stopping.
HERE="$(cd "$(dirname "$0")" && pwd)"
NAME="$1"
shift
PY="$(command -v python3 2>/dev/null || command -v python 2>/dev/null)"
if [ -z "$PY" ]; then
  echo "crew: no python on PATH, cannot run hook $NAME" >&2
  case "$NAME" in guard*) exit 2 ;; *) exit 0 ;; esac
fi
exec "$PY" "$HERE/$NAME.py" "$@"
