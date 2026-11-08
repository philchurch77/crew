---
name: work-the-inbox
description: "Maintainer only, in this repo: work the field-report inbox by cluster, from open issues to a seeded case, an agent edit, an evals run and a scoreboard row"
argument-hint: Empty to triage the inbox, or a cluster letter from the ledger to work it, e.g. "B"
disable-model-invocation: true
---

# Work the inbox

You are maintaining the crew, not sailing it. AGENTS.md sections 6 and 7
are the rules; `docs/field-reports/LEDGER.md` is the record. This skill
runs the loop in order and stops at the checkpoints. It runs anywhere with
git and Python; the evals themselves run on GitHub Actions.

Argument: **$ARGUMENTS**

## Empty argument: triage

1. List the inbox: `gh issue list --repo philchurch77/crew --label field-report --state open --json number,title,body`,
   plus any numbered file in `docs/field-reports/` with no ledger row.
2. For every report without a row, decide the agent, the kind (`fact` or
   `judgment`) and, for a judgment miss, the cluster: an existing letter
   or a new one.
3. **Facts: do them now.** One line in the Articles or the Captain, paid
   for by a cut in the same file. `python3 tools/budget.py` must pass.
   Set the row to `fixed`, bump the patch version, commit, push, and
   close each issue with its row as the comment.
4. **Judgment misses: ledger only.** Add the row as `clustered`. Name any
   cluster that has reached three reports. **Stop.** The developer
   chooses whether to work one.

## A cluster letter: work it

1. **Read** the cluster's reports and its plan section in
   `docs/plan-2026-11.md` if one exists.
2. **Seed** the miss in `plugins/crew/evals/_fixture/schoolapp/`, the
   smallest change that makes the defect real. Reproduce it by hand and
   paste the output. Add the reproduction to `tools/fixture_check.py`.
3. **Write the case** in `plugins/crew/evals/<case>/`: copy the nearest
   existing case, write the prompt the way the developer would type it
   and without any hint at the defect (a prompt that names the symptom
   is answered by plain Claude). One grader on the outcome with concrete
   PASS and FAIL conditions, one `dispatched-<agent>` grader. Add the row
   to the table in `evals/README.md`. Commit, push, and ask for one evals
   workflow run on the branch with the case name at one run per arm.
   **Stop.**
4. **Read the summary.** Three outcomes:
   - Crew fails, baseline fails: make the smallest edit that should turn
     it green, under budget, push, ask for one more run. **Stop.** When
     it passes, release (step 5).
   - Both pass: the model does the job. Set the rows to `fixed`, note
     "found by the model" in the fix column, keep the case. Release.
   - Crew passes, baseline fails: the crew already catches it. Same as
     above, with "caught by the crew" in the fix column.
5. **Release**: bump the version, add the SCORES row from the summary
   (crew / baseline per case run), set the ledger rows, close the issues
   with their rows, one commit, push, open the pull request.

## What you never do here

- Edit an agent for a judgment miss before a run has shown the crew arm
  failing it.
- Raise a word budget. Cut first; a budget rises only when the case fails
  without the words and no shorter edit passes, and the commit says so.
- Put anything from a real project into the fixture, a case or the ledger.
  Reports are already in fixture terms; keep them that way.
