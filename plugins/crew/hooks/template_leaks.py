#!/usr/bin/env python3
"""Catches developer text that will reach the page (article 7).

Django parses `{# #}`, `{{ }}` and `{% %}` on a single line only. Split any of
them across a newline and the opener is sent to the browser as text: a
comment becomes visible commentary, a tag becomes a TemplateSyntaxError at
render time. This shipped once, and a teacher read six developer notes above
her appraisal as error messages. A render test cannot catch it.

Run as a PostToolUse hook on Edit and Write, it scans the file just written
and reports every line with an unclosed opener. `before_stop.py` reuses
`scan()` for every changed template at the end of a turn, which also covers
files written from Bash.
"""
import json
import re
import sys

PAIRED = re.compile(r"\{#.*?#\}|\{\{.*?\}\}|\{%.*?%\}")
OPENER = re.compile(r"\{[#{%]")
CLOSER = re.compile(r"[#}%]\}")
HTML_COMMENT = re.compile(r"<!--")


def scan(path):
    """Return (leaks, html_comments): lists of (line_number, line_text)."""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
    except OSError:
        return [], []
    leaks, html = [], []
    for n, line in enumerate(lines, 1):
        rest = PAIRED.sub("", line)
        if OPENER.search(rest) or CLOSER.search(rest):
            leaks.append((n, line.strip()))
        if HTML_COMMENT.search(line):
            html.append((n, line.strip()))
    return leaks, html


def report(path, leaks, html):
    parts = []
    if leaks:
        listing = "\n".join(f"  line {n}: {text[:100]}" for n, text in leaks[:10])
        parts.append(
            f"{path} has a template construct opened on one line and closed on another. Django does not parse "
            f"across lines: a `{{# #}}` split like this renders as visible page text and a split `{{% %}}` or "
            f"`{{{{ }}}}` fails at render time (article 7).\n{listing}\n"
            "Keep `{# #}` on one line, or use `{% comment %} ... {% endcomment %}` for anything longer."
        )
    if html:
        listing = "\n".join(f"  line {n}: {text[:100]}" for n, text in html[:5])
        parts.append(
            f"{path} contains an HTML comment. Developer notes are never `<!-- -->`: invisible on screen, delivered "
            f"to every browser, readable in view-source (article 7). Use `{{% comment %}}` unless it must reach the "
            f"browser.\n{listing}"
        )
    return "\n\n".join(parts)


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    path = str((data.get("tool_input") or {}).get("file_path") or "")
    if not path.lower().endswith((".html", ".htm", ".djhtml")):
        return 0
    leaks, html = scan(path)
    if not leaks and not html:
        return 0
    out = {"hookSpecificOutput": {"hookEventName": "PostToolUse"}}
    if leaks:
        out["decision"] = "block"
        out["reason"] = report(path, leaks, html)
    else:
        out["hookSpecificOutput"]["additionalContext"] = report(path, leaks, html)
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
