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

Everything else in the fixture follows the Articles, so a finding outside this
table is either a real gap in the fixture or noise from the agent. Both are
worth knowing.

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
- `--allow-tools Bash Write Edit` is needed by the Gunner case only. Leave it
  off to run the read-only cases without granting anything.
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
wording, re-run with `--judge-model sonnet` before touching the rubric.

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
4. Add the defect to the table above.
