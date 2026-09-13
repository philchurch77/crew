---
type: llm
---

The project has exactly one cross-school access defect: `observation_detail` in `tolerance/views.py` calls `get_object_or_404(Observation, pk=pk)` with no school or ownership filter, so any logged-in user from any school can open any observation by changing the pk in the URL. The neighbouring `observation_edit` view filters by `pupil__school` correctly.

PASS if the response identifies `observation_detail` (or that exact `get_object_or_404` call) as the defect, states that a user from another school can read the record, and proposes a fix that filters by the user's school (for example adding `pupil__school=school` to the lookup, or filtering the queryset first). The response may also raise other findings.

FAIL if the response does not name that view or that call, if it reports `observation_edit` as the unfiltered view, or if it says the permissions are sound.
