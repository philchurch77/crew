---
name: gauntlet
description: >-
  MANDATORY review procedure before completing any change that touches pupil or
  child data. Load BEFORE reporting work complete whenever the change affects an
  app or model the project CLAUDE.md declares sensitive (by default the
  tolerance, sdq, flashcards or evaluation apps, and the Observation, WeeklyMap
  or SDQResponse models); any model, view, form, queryset, template or migration
  holding data linked to those; permission or access-control logic on such
  data; or any payload sent to an external API from those apps. Also load when
  the user asks to run the gauntlet, or asks whether a change is safe to ship
  where children data is involved.
---

# The Gauntlet

Running the gauntlet is the last thing that happens before a change touching
sensitive data is called done. It is not a favour to the user and it is not
something they have to remember to ask for. If the trigger conditions are met,
you run it.

## Why this exists

Article 0 of the Ship's Articles says what the data is and what a defect
costs. The scope is whatever the project `CLAUDE.md` declares as sensitive, or
the defaults named there, plus any model that links to a declared one.

## Before you start

State plainly which files this change touched and which of them fall in scope.
If you are not sure whether something is in scope, it is in scope.

## Each stage runs once

The Gauntlet is three sets of questions for three agents, plus a fourth when
the change can lose data, not extra dispatches. If the passage you are running already dispatches one of these
agents on the changed files, put that stage's questions into that dispatch and
the stage is satisfied by its answer. Cite the result; do not send the agent
back for a second look at the same files. Dispatch separately only the stages
nothing in the passage has covered.

## Stage 1 — Master-at-Arms

Dispatch the **master-at-arms** agent on the changed files. Give it the file
paths, not a description. Ask it to confirm each of these specifically:

1. No pupil name or identifying detail is sent to any external API. Check the
   payload that is actually constructed, not the variable name.
2. Every queryset returning sensitive data filters by the logged-in user or
   their school. No cross-user or cross-school access is reachable.
3. No sensitive data appears in URLs, logs, error messages, redirects or admin
   list displays.
4. Any new field on a sensitive model has a clear, minimal purpose. Nothing is
   collected without a stated reason.
5. Permissions are enforced in views, querysets and forms — not only in
   templates.

## Stage 2 — Lookout

Dispatch the **lookout** agent to walk the changed workflow as a real user.
Specifically:

- The core workflow completes without error.
- A logged-in user cannot reach another user's records by changing a PK or
  URL.
- The feature behaves correctly logged out, as the wrong user, and as the
  correct user. All three, not just the last.

Stage 1 and Stage 2 are independent. When both need dispatching, dispatch them
in parallel.

## Stage 3 — Proof, not opinion

Confirm there is a test that fails if the access control is removed. If there
is not, the **gunner** writes it and runs it. When the passage already
dispatches the Gunner, this is the first test it writes. A permission that is
correct today with no test protecting it is a permission that will regress.

## Stage 4 — Purser, when the change can lose data

This stage applies only when the change adds or alters a migration, changes a
field on a sensitive model, or edits a form or template that handles stored
sensitive text. A child's record that is lost is as much a breach as one that
is exposed. Dispatch the **purser** on those files, in parallel with Stages 1
and 2, and ask it to confirm:

1. No migration removes, renames, retypes or shrinks a column without a data
   migration that preserves the contents, and no `RunPython` body shortens or
   replaces existing text.
2. Every edit form renders the full stored value and re-renders bound on a
   validation error. Save, reload, re-save is byte-for-byte identical.
3. No cascade from a pupil, school or user silently deletes a child's history.

If the Purser says a migration is destructive, the task is not complete until
the data migration and backup it asks for exist.

## Report

- What Master-at-Arms flagged, and how each item was resolved.
- What Lookout found, and whether it ran the flow or read it.
- What the Purser flagged, if Stage 4 applied, and how each item was resolved.
- The access-control test, and its real run output.
- Verdict: **safe to ship** or **not safe to ship**.

## The hard rule

**If any stage raises a concern that is not resolved, the task is not complete.**
Do not mark it done. Do not bury it in a summary. Surface it at the top of your
report as a decision for the developer — especially anything that may need a
DPIA check before shipping. That judgement is theirs, not yours.
