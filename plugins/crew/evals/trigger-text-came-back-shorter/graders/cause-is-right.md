---
type: llm
---

`Observation.body` in `tolerance/models.py` is a `CharField(max_length=200)`, changed from a `TextField` by migration 0002. Free text longer than 200 characters is cut or rejected depending on the database, so what the teacher typed is not what was stored.

PASS if the response names `Observation.body` being a `CharField` with `max_length=200` (or migration 0002 shrinking it) as the cause of the shortened text.

FAIL if it does not identify that field limit as the cause.
