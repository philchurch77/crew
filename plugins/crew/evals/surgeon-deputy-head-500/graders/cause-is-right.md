---
type: llm
weight: 2
---

`_school_for` in `tolerance/views.py` returns `user.membership.school`. `Membership` is a `OneToOneField` from the user, so a user with no `Membership` row raises `RelatedObjectDoesNotExist` ("User has no membership") the moment any view calls `_school_for`. Every view in the app calls it, so the deputy head gets a 500 on every page, not only the dashboard. The dashboard is simply the page she opened first.

PASS if the response names the missing `Membership` (or "no membership", "not linked to a school", "user.membership") for the new user as the cause, and points at `_school_for` or the `user.membership` access in `tolerance/views.py` as where it fails.

FAIL if the response blames the dashboard's own code (the per-pupil loop, the scoring, the email, `latest.author`), the migration, permissions, or anything other than the missing Membership; or if it does not name the cause at all.
