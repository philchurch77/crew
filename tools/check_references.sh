#!/usr/bin/env bash
# Assemble the three reference sets into one throwaway Django project, as
# their READMEs say to, and run it: the starter, the house style on top,
# then the chat app. A reference that does not run is worse than none.
#
#   bash tools/check_references.sh
#
# Needs: pip install -r plugins/crew/skills/new-project/reference/requirements.txt anthropic PyYAML
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS="$ROOT/plugins/crew/skills"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

cp -r "$SKILLS/new-project/reference/." "$WORK/"
cp -r "$SKILLS/house-style/reference/static" "$WORK/static"
cp -r "$SKILLS/house-style/reference/templates/." "$WORK/templates/"
cd "$WORK"
export DEBUG=True

echo "== the palette passes its contrast check"
python "$SKILLS/house-style/reference/check_contrast.py" static/css/tokens.css > /dev/null

echo "== the starter alone"
python manage.py test -v 0

echo "== with the chat"
cp -r "$SKILLS/ai-features/chat-reference/chat" chat
python - <<'PY'
from pathlib import Path

settings = Path("config/settings.py")
text = settings.read_text()
text = text.replace('    "accounts",\n', '    "accounts",\n    "chat",\n', 1)
text = text.replace(
    '        "core.context_processors.names",\n',
    '        "core.context_processors.names",\n        "chat.context_processors.assistant",\n', 1,
)
text += '\nASSISTANT_NAME = "Assistant"\nAI_MODEL = "claude-opus-5-5"\nAI_EFFORT = "medium"\nAI_RUN_LIVE_TESTS = False\n'
settings.write_text(text)

urls = Path("config/urls.py")
text = urls.read_text()
marker = '    path("accounts/", include("accounts.urls")),\n'
assert marker in text, "config/urls.py no longer has the line this script extends"
urls.write_text(text.replace(marker, marker + '    path("chat/", include("chat.urls")),\n', 1))
PY
grep -q '"chat",' config/settings.py
python manage.py makemigrations chat -v 0
python manage.py test -v 0
python manage.py makemigrations --check --dry-run > /dev/null

echo "the references run"
