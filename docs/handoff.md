# Handoff, 21 September 2026

Read this, then AGENTS.md sections 6 and 7, before touching anything.
Delete this file when its work is done; AGENTS.md is the standing guide.

## Where things stand

The crew has an improvement loop as of today: a scoreboard
(`plugins/crew/evals/SCORES.md`), word budgets (`tools/budgets.json`,
checked by `tools/budget.py`), a fixture check (`tools/fixture_check.py`),
CI for all three on every push, a `/field-report` command that files a
miss as an issue labelled `field-report`, and two new eval cases (Surgeon,
Lookout). Version is 2.15.0.

Evals run on the maintainer's laptop, not in CI. The Windows clone runs the
eight cases that do not grant Bash; the WSL2 clone at `~/crew` runs the
three that do (Gunner, Surgeon, Lookout) and can run everything. Both bill
the subscription. `.github/workflows/evals.yml` is the paid route and runs
by hand only. One case at a time, `--runs 1`, `--judge-model sonnet`.

## Scores so far (one run per arm unless noted)

| Case | Crew | Plain | Agent called | Read |
|---|---|---|---|---|
| Purser | 1.00 | 0.67 | yes | Clear win; plain misses the cascade. 3 runs per arm. |
| Chart | 0.86 | 0.14 | yes | Clear win; plain wrote a plan file without asking. |
| Gunner | 1.00 | 1.00 | yes | Draw at 8x the cost. Case too easy. Issue #10. |
| Surgeon | 0.71 | 0.86 | no | Never dispatched. Case too easy. Issue #9. |
| Lookout | 1.00 | 0.83 | no | Never dispatched, but crew arm walked the flow. |

Six cases have no number yet: Carpenter, Bosun, Master-at-Arms, the
trigger case, and the two Build cases.

## What was tried for routing, in order

1. Stronger descriptions on Surgeon and Lookout ("use proactively, before
   answering"), paid for under budget by trimming character text. Re-run
   of Surgeon: still not dispatched. Not the lever.
2. Both prompts now start with `/crew:captain` (2.14.1), because the
   Captain's Fix passage starts with the Surgeon and its Look passage sends
   whole-workflow QA to the Lookout, and both Captain cases dispatched.
   **Run, and it worked:** both agents dispatched (Agent called 1x).
   Surgeon 0.71 / 0.71, Lookout 0.83 / 0.67.

## First job: an open question the last run raised

With the agents dispatched, `Bash called 0x` in both crew arms. Yet the
Lookout's report passed the `labelled-ran` judge, and the Surgeon's own
rules say build a loop before naming a cause. Earlier in the day, when the
main session did the walking itself, the Lookout case counted Bash 3x.
Two readings, and the difference matters for every case with a
`tool_used` grader:

- The `tool_used` grader counts only the main session's calls, not a
  subagent's. Then every Bash grader on a dispatched agent is blind, and
  the Purser, Gunner and Chart scores need re-reading too (the Gunner's
  `tests-were-run` may have counted the Captain's run, not the Gunner's).
- The agents genuinely ran nothing. Then the Lookout labelled a read as
  "ran", which breaks article 10, and the Surgeon skipped its loop. Both
  are agent failures to fix under budget.

The docs do not say (checked 2026-09-20 against
code.claude.com/docs/en/plugin-evals). Settle it empirically: run
`lookout*` with `--keep-temp --ablation none --runs 1`, open the kept
directory's transcript and its `subagents/` folder, and look for Bash
calls inside the Lookout's own transcript. If they are there, the grader
is blind to subagents and the method graders need a `trace` target or a
different design. If they are not, the agents are at fault.

## Done on 21 September: candidate 1 of #9 and #10, run, both draws

Seeded, reproduced by hand, in `tools/fixture_check.py`, cased (2.15.0)
and run on WSL2 at one run per arm. Both scored 1.00 / 1.00.

- `surgeon-third-bad-day`: the Surgeon was dispatched and Bash ran 6x in
  the crew arm. But the baseline also built a loop (Bash 2x), found the
  boundary record, and ruled out an alternative on two votes of three.
  A wrong-number symptom with data in the database was enough to make
  plain Claude run it.
- `gunner-cross-school-test` with the `?pupil=` hole: both arms wrote
  the parameter test, ran it, and reported it failing. Plain Claude does
  not stop at the detail view.
- Read against AGENTS.md section 7 ("Baselines"): the model does the
  method on its own. That is a signal to cut, and a roster question for
  the Gunner (issue #10 says so). Before acting on one run per arm, run
  each at `--runs 3` for a real score; a draw at three runs is a draw.
- The fixture now has a `seed_demo` management command and `seed.sh` takes
  `--demo`. The Carpenter and Master-at-Arms may remark on the command;
  read those as noise unless the remark is right.
- Bash 6x with the Surgeon dispatched is the first evidence that the
  `tool_used` grader does see a subagent's calls, which would make
  yesterday's 0x a real agent miss. The `--keep-temp` check below still
  settles it, because the Captain may have run those commands itself.

## The work queued

- Run the six unmeasured cases and fill the row.
- Later: a second fixture in a different domain, against overfitting to
  the school app.

Each new case follows AGENTS.md section 7: seed, reproduce by hand, add to
`tools/fixture_check.py`, write the case, watch it fail, then and only then
edit the agent, cutting to stay in budget. Record the row.

## Things learned today that are not written elsewhere

- The eval harness wants `case.yaml` to be one four-line object; the
  description, tags and run settings live in `prompt.md` frontmatter.
- An `llm` grader can pass on a described action that never happened.
  When a `tool_used` grader and a judge disagree, trust the tool count.
  The Surgeon's `loop-was-red` was removed for this.
- A crew-arm run costs 2 to 4 dollars against an API key and 5 to 8
  minutes; a baseline run 35 cents and 90 seconds. Judge cost is small.
- Native Windows has no Claude Code sandbox, so the harness refuses to
  grant Bash there. WSL2 with `bubblewrap` and `socat` is the route.
- Windows Git Bash's `python3` is often the Store stub; `seed.sh` now
  tries `python` too and uses `.venv/Scripts` when `.venv/bin` is absent.
- Three clones exist: GitHub, Windows (`~\dev\crew`, the junction target)
  and WSL2 (`~/crew`). Merge on the website, then pull both. Never edit
  in two places at once.
- The `field-report` label must exist on the repo for `gh issue create`
  to work; the command falls back to printing if not.
