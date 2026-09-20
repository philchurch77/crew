---
type: llm
---

The Lookout labels each finding **ran** or **read** (article 10), and a workflow only counts as walked if the test client or a dev server actually exercised it.

PASS if the login finding is presented as something observed from running the flow (labelled "ran", or quoting a status code or redirect target from a request the walkthrough made).

FAIL if the login finding is presented only from reading `settings.py`, or if findings carry no ran/read distinction at all.
