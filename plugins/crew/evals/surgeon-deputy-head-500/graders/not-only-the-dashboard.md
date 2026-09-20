---
type: llm
---

The user reported the dashboard. The real defect is in `_school_for`, which every view in `tolerance/views.py` calls, so the deputy head cannot open any page of the app.

PASS if the response says, in any wording, that the failure is not specific to the dashboard: that the observation list, the form or "every page" would fail for her too, or that the shared helper is the problem rather than the dashboard view.

FAIL if the response treats the defect as belonging to the dashboard view alone.
