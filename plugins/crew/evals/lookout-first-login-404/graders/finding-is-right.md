---
type: llm
weight: 2
---

`config/settings.py` sets `LOGIN_URL` but not `LOGIN_REDIRECT_URL`. Django's default is `/accounts/profile/`, which this project does not route. A teacher who opens the login page directly and logs in is redirected to `/accounts/profile/` and sees a 404. Logging in via a `?next=` redirect from a protected page still works, which is why a walkthrough that starts on a protected page, or uses `force_login`, never sees it.

PASS if the response reports that after logging in from the login page the teacher lands on a 404 or a page that does not exist (naming `/accounts/profile/`, or `LOGIN_REDIRECT_URL`, or describing the landing page as missing or broken), and rates it as a real problem for the first login.

FAIL if the login flow is reported as working, or the post-login landing page is not mentioned at all.
