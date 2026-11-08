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
2. Read the ledger. For every report without a row, read the report and
   decide: which agent, which cluster (an existing letter, or a new one
   when no existing pattern fits), and the kind, `judgment` or `fact`.
   A judgment miss is one where the agent had what it needed and chose
   wrong. A fact miss is knowledge or a hygiene rule it lacked.
3. Propose the new rows and, if a new cluster, its seed and case in two
   lines each. Show the ledger diff. **Stop.** The developer chooses the
   cluster to work, and the next invocation carries its letter.

## A cluster letter: work it

Do the steps in this order and do not skip one. Each step ends with its
evidence in the conversation.

1. **Read** the cluster's reports in full and its plan section in
   `docs/plan-2026-11.md` if one exists.
2. **Seed** the miss in `plugins/crew/evals/_fixture/schoolapp/`. The
   smallest change that makes the defect real. Reproduce it by hand with
   `manage.py shell` or the test client and paste the output.
3. **Keep the reproduction**: add it to `tools/fixture_check.py` and run
   the script; it must fail on a fixture without the seed and pass with it.
4. **Write the case** in `plugins/crew/evals/<case>/`: copy the nearest
   existing case, write the prompt the way the developer would type it
   (through `/crew:captain` when that is how they would ask), one grader
   on the outcome with concrete PASS and FAIL conditions, one
   `dispatched-<agent>` grader. Add the row to the table in
   `evals/README.md`.
5. **Fact rows** in the cluster: make the one-line edit now, paid for by a
   cut in the same file. Run `python3 tools/budget.py`.
6. **Commit and push** the branch with the seed, the check, the case and
   the fact edits, and nothing else yet. Tell the developer to run the
   evals workflow from the Actions tab on this branch with the case name
   at one run per arm, and to paste the job summary back. **Stop.**
7. When the summary comes back: the crew arm must **fail** the new case.
   If it passes, the agent did not miss it; the report was about routing
   or wording, and the fix is the description or the Captain, not the
   agent. Say so and stop.
8. **Edit the agent**: the smallest change that should turn the case
   green, paid for by a cut. `python3 tools/budget.py` must pass. Run
   `python3 plugins/crew/hooks/selftest.py` if a hook changed.
9. **Push** and ask for the same workflow run again. **Stop.** The case
   must now pass on the crew arm with the baseline delta intact.
10. **Push** and ask for the whole suite at one run per arm. **Stop.** No
    case's delta may drop below its last row in `SCORES.md`.
11. **Release**: bump `version` in `plugins/crew/.claude-plugin/plugin.json`,
    fill the `SCORES.md` row from the summary, set the ledger rows to
    `fixed` with the version, close each issue with its row as the comment
    (`gh issue close <n> --repo philchurch77/crew --comment "<row>"`), and
    commit all of it as one commit with the case named in the message.

## What you never do here

- Edit an agent before step 7 has shown the case failing.
- Raise a word budget. Cut first; a budget rises only when the case fails
  without the words and no shorter edit passes, and the commit says so.
- Put anything from a real project into the fixture, a case or the ledger.
  Reports are already in fixture terms; keep them that way.
