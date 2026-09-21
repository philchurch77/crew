---
type: llm
weight: 2
---

The dashboard in `tolerance/views.py` counts observations with `observed_on__gte=since` where `since = date.today() - timedelta(weeks=4)`. That window is 29 days wide (the boundary day and the 28 after it), while the page and the alert email call it "the last four weeks". The seeded data (`tolerance/management/commands/seed_demo.py`) gives Priya Nair dysregulated observations 2, 9 and 28 days ago. The one 28 days ago sits on the boundary and is counted, which makes three and rates her high. The rows are not duplicated, every mood was saved correctly, and the threshold of three is what the school asked for.

PASS if the response finds the third dysregulated observation dated 28 days ago and says it is counted because the dashboard's window includes the boundary day (naming `observed_on__gte`, `timedelta(weeks=4)`, `since`, "29 days", "inclusive", "off by one" or any equivalent), in `tolerance/views.py`.

FAIL if the response blames a duplicate observation, a wrongly entered mood, the wrong pupil, the scoring formula, the `dysregulated >= 3` threshold, the form, the seed data being wrong, or anything other than the date window's boundary; or if it names no cause; or if it says the dashboard is right and the teacher is wrong.
