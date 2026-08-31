---
name: gauntlet
description: >-
  MANDATORY review procedure before completing any change that touches pupil or
  child data. Load this BEFORE reporting work complete whenever the change
  affects the tolerance, sdq, flashcards or evaluation apps; any model, view,
  form, queryset, template or migration holding pupil-linked data
  (Observation, WeeklyMap, SDQResponse or similar); permission or access-control
  logic on such data; or any payload sent to an external API from those apps.
  Also load when the user asks to run the gauntlet, or asks whether a change is
  safe to ship where children data is involved.
---

# The Gauntlet

Running the gauntlet is the last thing that happens before a change touching
pupil data is called done. It is not a favour to the user and it is not
something they have to remember to ask for. If the trigger conditions are met,
you run it.

## Why this exists

This platform holds **Article 9 special category data about children in care** —
names, emotional states, observed behaviours, safeguarding context. The
consequence of a permissions defect here is not a bug report. It is a child data
breach, a notifiable incident, and the end of the client relationship.

The apps in scope are `tolerance`, `sdq`, `flashcards` and `evaluation`, plus
any model that links to a pupil record.

## Before you start

State plainly which files this change touched and which of them fall in scope.
If you are not sure whether something is in scope, it is in scope.

## Stage 1 — Master-at-Arms

Dispatch the **master-at-arms** agent on the changed files. Give it the file
paths, not a description. Ask it to confirm each of these specifically:

1. No pupil name or identifying detail is sent to any external API. Check the
   payload that is actually constructed, not the variable name.
2. Every queryset returning pupil-linked data filters by the logged-in user or
   their school. No cross-user or cross-school access is reachable.
3. No pupil data appears in URLs, logs, error messages, redirects or admin list
   displays.
4. Any new field on a pupil-linked model has a clear, minimal purpose. Nothing
   is collected without a stated reason.
5. Permissions are enforced in views, querysets and forms — not only in
   templates.

## Stage 2 — Lookout

Dispatch the **lookout** agent to walk the changed workflow as a real user.
Specifically:

- The core workflow completes without error.
- A logged-in user cannot reach another user records by changing a PK or URL.
- The feature behaves correctly logged out, as the wrong user, and as the
  correct user. All three, not just the last.

Stage 1 and Stage 2 are independent. Dispatch them in parallel.

## Stage 3 — Proof, not opinion

Confirm there is a test that fails if the access control is removed. If there is
not, dispatch the **gunner** agent to write it and run it. A permission that is
correct today with no test protecting it is a permission that will regress.

## Report

- What Master-at-Arms flagged, and how each item was resolved.
- What Lookout found.
- The access-control test, and its real run output.
- Verdict: **safe to ship** or **not safe to ship**.

## The hard rule

**If any stage raises a concern that is not resolved, the task is not complete.**
Do not mark it done. Do not bury it in a summary. Surface it at the top of your
report as a decision for the developer — especially anything that may need a
DPIA check before shipping. That judgement is theirs, not yours.
