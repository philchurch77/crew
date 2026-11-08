---
type: llm
weight: 2
---

`observation_autosave` in `tolerance/views.py` is decorated `@login_required @require_POST` and is otherwise correct: school-filtered, validated, JSON on success and on a 400. The defect is what a signed-out caller receives. When the teacher's session has expired, `@login_required` answers the POST with a 302 to `/login/?next=...`. `fetch()` follows redirects, lands on the login page with a 200 HTML response, so `r.ok` is true; `r.json()` fails and falls back to `{}`; `tolerance/static/tolerance/autosave.js` then sets "Saved", advances `saved`, and the `beforeunload` warning stands down. The 401/403 "signed out" branch never fires. The teacher closes the tab and the text is gone while the page said Saved.

PASS if the response states that a signed-out (expired-session) autosave is redirected to the login page, that the script or fetch treats the redirected 200 as a successful save (shows Saved, or drops the unsaved warning, or the text is silently lost), rates it Critical or High, and proposes a fix: the endpoint returns 401 or 403 JSON instead of redirecting, and/or the script treats `response.redirected`, a non-JSON reply or a missing `ok: true` as a failed save.

FAIL if the response says the endpoint safely refuses anonymous callers because `@login_required` is present, says the 401/403 branch covers a signed-out teacher, does not consider what a signed-out request receives, or names the redirect but rates it Medium or Low.
