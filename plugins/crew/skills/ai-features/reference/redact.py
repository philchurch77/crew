"""Nothing identifying leaves the system (article 13). The caller passes the
names it knows for the pupil; patterns catch what it does not."""
import re

DATE = re.compile(r"\b\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4}\b")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE = re.compile(r"\b(?:\+44\s?\d|0\d)[\d\s\-]{8,12}\d\b")


def redact(text, names=()):
    """Return (redacted text, number of replacements). Longest names first so
    a surname inside a full name is not left behind."""
    count = 0
    for name in sorted({n.strip() for n in names if n and len(n.strip()) > 1}, key=len, reverse=True):
        text, n = re.subn(r"\b" + re.escape(name) + r"\b", "[PUPIL]", text, flags=re.IGNORECASE)
        count += n
    for pattern, token in ((EMAIL, "[EMAIL]"), (PHONE, "[PHONE]"), (DATE, "[DATE]")):
        text, n = pattern.subn(token, text)
        count += n
    return text, count
