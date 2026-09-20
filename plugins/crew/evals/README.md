# Crew evals

A measured crew beats a trusted one. This suite gives every agent a Django
project with a defect it is meant to catch, and grades whether it caught it.
Run it after any change to an agent, a skill or the Articles; the score is the
review.

## The fixture

`_fixture/schoolapp/` is a small Django project: a `schools` app (School,
Membership, Pupil) and a `tolerance` app (Observation). Its `CLAUDE.md`
declares `tolerance`, `Observation` and `Pupil` sensitive. It carries five
seeded defects, each the target of one case:

| Defect | Where | Case |
|---|---|---|
| `get_object_or_404(Observation, pk=pk)` with no school filter | `tolerance/views.py` `observation_detail` | `master-at-arms-unfiltered-detail` |
| A `{# #}` comment split across three lines, rendered as page text | `tolerance/templates/tolerance/observation_form.html` | `bosun-split-comment` |
| Migration 0002 shrinks `Observation.body` from `TextField` to `CharField(200)`; `Observation.pupil` cascades | `tolerance/migrations/0002_shorten_body.py`, `tolerance/models.py` | `purser-destructive-migration`, `trigger-text-came-back-shorter` |
| Four queries per pupil in a loop, plus scoring rules and email in the view | `tolerance/views.py` `dashboard` | `carpenter-oversized-dashboard` |
| Empty `tolerance/tests.py` | | `gunner-cross-school-test` |
| `_school_for` reads `user.membership` unguarded; a user with no Membership raises on every page | `tolerance/views.py` `_school_for` | `surgeon-deputy-head-500` |
| No `LOGIN_REDIRECT_URL`; a login from the login page lands on a 404 at `/accounts/profile/` | `config/settings.py` | `lookout-first-login-404` |
| A feature request: an "agreed action" field on Observation | the whole fixture | `captain-build-heaves-to`, `captain-build-weighs-anchor` |
| A whole new app: attendance registers, too big for one passage | the whole fixture | `captain-chart-heaves-to` |

Everything else in the fixture follows the Articles, so a finding outside this
table is either a real gap in the fixture or noise from the agent. Both are
worth knowing. `tools/fixture_check.py` at the repo root reproduces every
row of this table against the fixture and fails if one has gone; CI runs it.

The Surgeon and Lookout cases test method as much as detection. The Surgeon
is handed "the dashboard 500s for one new user" and must build a red loop
before naming a cause, name the missing Membership rather than the dashboard
code, say the failure is not the dashboard's alone, and change nothing. The
Lookout is asked to walk the app as a new teacher from the login page; the
defect is one that `force_login` never meets, so a walkthrough that starts
past the login page passes every view and misses it. Both need Django, so
their scaffolds build the `.venv` like the Gunner's.

The Captain cases test the passage rather than a finding. `captain-chart-heaves-to`
hands the Captain a whole attendance app and expects the Chart passage: the
Quartermaster dispatched in grilling mode, a round of numbered questions with
recommended answers as the final message, and no plan, chart file or code
before the developer has answered. The two Build cases share one feature. The first
types `/crew:captain` with the feature and expects the Captain to read the
water, name the passage, send the Quartermaster aloft, show the plan and
stop, with no code written. The second resumes that exact conversation from
`history.jsonl` (a transcript saved from a run of the first) with the user
saying aye, and expects the rest of the passage: the change made, the four
reviewers dispatched, the Gunner after them, the Lookout last, and a log
whose Tests, Gauntlet and Purser lines report what really happened. If you
change the Captain's checkpoint wording enough that the saved transcript no
longer matches, re-record it: run the first case with `--keep-temp` and copy
the session `.jsonl` from the kept directory's `config/projects/` tree.
When the second case runs, the harness writes the resumed session's own
transcript and a `subagents/` folder beside `history.jsonl`, named by the
session id. Those are run output and are ignored by git; only
`history.jsonl` is the fixture.

Each case's `scaffold.sh` copies the fixture into the run's empty workspace and
commits it. The Gunner case also needs Django importable; its scaffold builds a
`.venv` if the system interpreter lacks it.

## Running

From the plugin root:

```
cd plugins/crew
claude plugin eval . --scaffold --trust-plugin --allow-tools Bash Write Edit
```

- `--scaffold` is required; without it every case starts in an empty
  directory and scores zero.
- `--allow-tools Bash Write Edit` is needed by the Gunner case, and by any
  agent with `memory: project`: without Write the agent cannot keep its
  memory, and a run can end on a note about that instead of the answer.
  Grant it for the whole suite. `guard_edit` still confines the reviewers
  to their memory directory.
- `--case 'purser*'` runs one case. `--runs 1` is enough while iterating;
  the default three runs per arm is for a real score.
- `--ablation none` skips the no-plugin baseline. The default compares the
  crew against plain Claude and reports the delta, which is the number that
  says whether the crew earns its keep.
- `--max-cost-usd` caps a run. The full suite with baseline is roughly
  thirty agent runs.

Results land in `evals/results/<timestamp>/` with an HTML report; that
directory is ignored by git.

## Reading a result

Each case has one or more outcome graders (a regex on the final message, an
`llm` rubric with explicit PASS and FAIL conditions, or the contents of a file
the run produced) and one `dispatched-<agent>` grader. The dispatch grader is
marked `arm: with-only`, so it does not count toward the score; it is the
indicator that the right agent was chosen. Read the two together:

- Outcome fails, dispatch passes: the agent was called and missed the defect.
  Fix the agent.
- Outcome fails, dispatch fails: the agent was never called. Fix its
  `description`, or the Captain's routing.
- Outcome passes, dispatch fails: the main session found it alone. Fine for
  the score, but the agent's trigger phrases are not matching that wording.
- Baseline delta near zero: plain Claude does as well. Either the defect is
  too easy or the agent adds nothing on it. Make the case harder before
  making the agent longer.

An `llm` grader's judge is Haiku by default. If a correct answer is failing on
wording, re-run with `--judge-model sonnet` before touching the rubric. The
Captain's log rubric is the known case: a log that says "tests written, not
run, because the shell failed" is honest under article 10 and passes with
Sonnet, but Haiku fails it three votes to none. Run the three Captain cases,
the Surgeon case and the Lookout case with `--judge-model sonnet`.

## Recording a result

`SCORES.md` beside this file carries one row per plugin version that
changed an agent, a skill, the Articles or the Captain: crew score and
baseline score per case. Fill it from the HTML report when you bump the
version. The results directory is ignored by git, so the scoreboard is the
only place a score survives, and the only way to see whether the last
change helped.

## Adding a case

1. Seed the defect in `_fixture/schoolapp/` and prove it by hand: the
   Master-at-Arms defect was confirmed by fetching the detail page as a user
   from another school and getting a 200; the Bosun defect by finding `{#`
   in the rendered form. Do not write a case for a defect you have not seen.
2. Copy an existing case directory. Write the prompt the way you would type
   it, without naming the agent: the case tests routing as much as detection.
3. Give it one grader on the result and one `dispatched-<agent>` grader.
   Write `llm` rubrics as concrete PASS and FAIL conditions that name the
   file and the defect, so a small judge cannot pass a vague answer.
4. Add the defect to the table above, and the reproduction to
   `tools/fixture_check.py`.

## When an agent misses something in a real project

`/field-report` in that project files the miss as an issue labelled
`field-report`; that label is the inbox. Do not edit the agent. Seed the miss here first, prove it by hand, write
the case, watch it fail, and only then make the smallest change to the
agent that turns it green. Then run the whole suite and record the row.
The agents have word budgets (`tools/budgets.json`) for exactly this
reason: a paragraph per miss is how a good agent turns into a long one.
AGENTS.md section 7 has the full rule.
