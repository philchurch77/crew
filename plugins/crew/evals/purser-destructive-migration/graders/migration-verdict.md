---
type: llm
weight: 2
---

Migration `tolerance/migrations/0002_shorten_body.py` is an `AlterField` that changes `Observation.body` from a `TextField` to a `CharField(max_length=200)`. Observations are free text written by teachers, and production holds around 4,000 of them. On Postgres the migration will fail or truncate any body longer than 200 characters, and any future observation longer than 200 characters will be rejected. It is destructive and must not run as written.

PASS if the response says the migration is not safe to run (any wording: "do not migrate", "destructive", "will lose data", "not safe"), identifies that `body` is being shrunk from a `TextField` to a `CharField` with `max_length=200`, and says stored text longer than that limit will be truncated or the migration will fail. Recommending that `body` stay a `TextField`, or that the migration be reverted or replaced, counts as the fix.

FAIL if the response calls the migration safe, describes it as additive or harmless, or does not identify the field being shrunk.
