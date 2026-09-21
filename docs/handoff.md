# Handoff, 21 September 2026

Read this, then AGENTS.md sections 6 and 7, before touching anything.
Delete this file when its work is done; AGENTS.md is the standing guide.

## Where things stand

The crew has an improvement loop as of today: a scoreboard
(`plugins/crew/evals/SCORES.md`), word budgets (`tools/budgets.json`,
checked by `tools/budget.py`), a fixture check (`tools/fixture_check.py`),
CI for all three on every push, a `/field-report` command that files a
miss as an issue labelled `field-report`, and two new eval cases (Surgeon,
Lookout). Version is 2.15.1.

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

## The grader question, answered by the counts

Run 21 September, `lookout*` crew arm with `--keep-temp`: Lookout
dispatched, Bash 10x. `surgeon-third*` at 3 runs: Surgeon dispatched,
Bash 7, 7, 8. Yesterday's 0x with the same agents dispatched was not the
grader going blind; the counts move with what the agents do. The kept
directory is `/tmp/claude-eval-KC7BGK` on WSL2 (`chmod 700` it and its
`sealed/` as the harness says). Its `subagents/` transcript settles the
last doubt, whether the Bash calls were the Lookout's or the Captain's,
and shows why `labelled-ran` failed: the Lookout walked the flow (10
Bash calls, finding right) and the final report still carried no
ran/read label. Either the Lookout did not label or the Captain's log
dropped it. Read: the Lookout's own transcript labelled every finding and even
listed what it could only read. The Captain's log turned twenty-one
findings into one line per agent. Fixed in 2.15.1 in `captain.md`,
section 5: on a Look passage, every finding with its severity and label.
Confirmed at 3 runs per arm: 1.00 / 0.89, labelled-ran green on every
crew run. The Captain still sends four agents on that Look (Lookout,
Master-at-Arms, Purser, Bosun) at 5 to 7 a run against 1 for the
baseline. Whether "what's broken or confusing from her point of view"
should dispatch more than the Lookout and Bosun is an open routing
question with no case behind it. Do not touch it until a field report
or a case says the extra agents found nothing the Lookout did not.

## Where this leaves the loop, 21 September

The improvement loop has now been run end to end once: a case failed
(labelled-ran), the transcript said which file, the smallest edit went
in under budget, and the re-run went green with the delta intact. The
grader question is closed. The next misses should come from real
projects through `/field-report`, not from harder fixture cases: two
"make it harder" rounds in a row produced one measuring case (Surgeon)
and one draw (Gunner). Work the `field-report` inbox in the section 7
order.

Still open, in order of value:

- Issue #10's roster question on the Gunner (above).
- The six cases with no number: Carpenter, Bosun, Master-at-Arms, the
  trigger case, and the two Build cases. All run on Windows without
  Bash except as noted in the README. One run per arm first.
- A second fixture in another domain, against overfitting to the school
  app. Only after the field-report inbox has produced a few cases.

## Done on 21 September: candidate 1 of #9 and #10, run at 3 per arm

Seeded, reproduced by hand, in `tools/fixture_check.py`, cased (2.15.0)
and run on WSL2, first at one run per arm (both 1.00 / 1.00), then at
three.

- `surgeon-third-bad-day`: crew 1.00 / baseline 0.76. The baseline
  skipped the loop on two runs of three and named the cause by reading
  anyway; the third run built a loop but ruled nothing out. The case
  now measures the Surgeon's method. Issue #9 can close with the row.
- `gunner-cross-school-test` with the `?pupil=` hole: 1.00 on all six
  runs. Crew run 2 never dispatched the Gunner and still scored 1.00 at
  a quarter of the cost. Plain Claude sends the parameter, runs the
  suite and reports the failure every time. Issue #10 said what this
  means: a roster question for AGENTS.md section 8, not a longer Gunner.
  The Gunner still owns two things the case does not measure: the
  guard-git and guard_tree hooks, and the Gauntlet's test stage. Decide
  whether those need an agent or a Captain step. A cheaper first move
  is the section 7 experiment: cut `gunner.md` hard and watch the score
  hold.
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
