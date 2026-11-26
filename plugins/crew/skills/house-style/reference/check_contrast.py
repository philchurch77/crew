"""Check a client's palette against the house style's contrast rules.

    python check_contrast.py path/to/tokens.css

Exits 1, naming each failing pair, if a colour set in the Brand block (or
anywhere else in the file) falls under WCAG 2.2 AA where it is used.
Standard library only.
"""
import re
import sys

# (foreground, background, minimum ratio, where it is used)
PAIRS = [
    ("--color-ink", "--color-page", 4.5, "body text on the page"),
    ("--color-ink", "--color-surface", 4.5, "body text on a card"),
    ("--color-ink-muted", "--color-page", 4.5, "muted text on the page"),
    ("--color-ink-muted", "--color-surface", 4.5, "muted text on a card"),
    ("--color-ink-muted", "--color-surface-2", 4.5, "the plain pill"),
    ("--color-primary", "--color-page", 4.5, "a link on the page"),
    ("--color-primary", "--color-surface", 4.5, "a link on a card"),
    ("--color-primary-strong", "--color-surface", 4.5, "a hovered link"),
    ("--color-on-primary", "--color-primary", 4.5, "the primary button"),
    ("--color-on-primary", "--color-primary-strong", 4.5, "the primary button, hovered"),
    ("--brand-tint-ink", "--brand-tint", 4.5, "the brand pill"),
    ("--color-ink", "--brand-tint", 4.5, "your turn in a chat, the open chat's row"),
    ("--color-on-bar", "--brand-bar", 4.5, "the product name on the bar"),
    ("--brand-bar-link", "--brand-bar", 4.5, "links on the bar"),
    ("--brand-bar-accent", "--brand-bar", 3.0, "the current-page line"),
    ("--color-ink", "--color-notice", 4.5, "the bar's notice pill"),
    ("--ring", "--color-surface", 3.0, "focus ring on a card"),
    ("--ring", "--color-page", 3.0, "focus ring on the page"),
    ("--ring", "--brand-bar", 3.0, "focus ring on the bar"),
    ("--color-input-line", "--color-surface", 3.0, "a field's edge"),
    ("--color-danger", "--color-surface", 4.5, "an error under a field"),
    ("--color-danger-ink", "--color-danger-bg", 4.5, "an error notice"),
    ("--color-warn-ink", "--color-warn-bg", 4.5, "a warning notice"),
    ("--color-good-ink", "--color-good-bg", 4.5, "a success notice"),
]


def read_tokens(path):
    text = open(path, encoding="utf-8").read()
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return dict(re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", text))


def resolve(name, tokens, seen=()):
    if name in seen or name not in tokens:
        raise ValueError(f"{name} is not set")
    value = tokens[name].strip()
    alias = re.fullmatch(r"var\((--[\w-]+)\)", value)
    if alias:
        return resolve(alias.group(1), tokens, seen + (name,))
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        raise ValueError(f"{name} must be a six-digit hex colour, not {value!r}")
    return value


def luminance(hex_colour):
    def channel(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (int(hex_colour[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def contrast(a, b):
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def main(path):
    tokens = read_tokens(path)
    failures = 0
    for fg, bg, minimum, use in PAIRS:
        try:
            ratio = contrast(resolve(fg, tokens), resolve(bg, tokens))
        except ValueError as error:
            print(f"FAIL  {use}: {error}")
            failures += 1
            continue
        ok = ratio >= minimum
        failures += not ok
        print(f"{'ok  ' if ok else 'FAIL'}  {ratio:5.2f}:1 (needs {minimum}:1)  {fg} on {bg}: {use}")
    return 1 if failures else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
