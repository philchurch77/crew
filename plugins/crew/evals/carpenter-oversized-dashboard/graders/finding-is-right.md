---
type: llm
---

The `dashboard` view in `tolerance/views.py` loops over every pupil in the school and, for each one, runs four separate queries (`count()` three times on filtered querysets plus `.first()`), then also touches `latest.author`. That is roughly five queries per pupil, so 300 pupils is about 1,500 queries per page load. The same function also holds the concern-score formula and the high/medium/low thresholds, sorts in Python, and sends email. Those are business rules that belong on the model, a queryset, or a service function, not in the view.

PASS if the response (a) identifies the queries inside the per-pupil loop as the performance problem and recommends replacing them with a single annotated queryset (`annotate`, `Count`, conditional aggregation, `prefetch_related` or `select_related` all count), and (b) identifies that the scoring or threshold rules and/or the email sending should move out of the view into a model method, manager, queryset or service function.

FAIL if either the loop queries or the misplaced business rules are missed, or if the response recommends adding a third-party package as the fix.
