---
type: llm
---

`Observation.pupil` in `tolerance/models.py` is a `ForeignKey(Pupil, on_delete=models.CASCADE)`. Deleting a pupil silently deletes every observation written about them.

PASS if the response mentions that the `pupil` foreign key on `Observation` cascades and that deleting a pupil would delete the pupil's observations, or otherwise flags `on_delete=CASCADE` on that relationship as a data-loss risk.

FAIL if the cascade is not mentioned at all.
