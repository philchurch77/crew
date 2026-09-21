# The Crew

This repository is a Claude Code plugin. It carries a crew of Django agents, a
Captain who dispatches them, and the standards they all work to. Installed into
a project, the whole crew comes with it.

This file is the maintainer's guide. **It does not ship with the plugin.**
Nothing at the repo root is loaded into a project that installs the crew; only
`plugins/crew/` is. The rules the crew works to live in the `ships-articles`
skill, the Gauntlet lives in the `gauntlet` skill, and the Captain's procedure
lives in `commands/captain.md`. Edit those to change behaviour. Edit this file
to explain it.

`CLAUDE.md` imports this file so sessions in this repo read it.

---

## 1. What the crew is for

1. **The crew serves Django work.** Every agent assumes Django, a real client,
   and sensitive data until the project says otherwise. Keep them specific. A
   generic agent is a worse agent, and so is a generic command.
2. **Permissions are filtered, never hidden.** The single standard the whole
   crew exists to enforce. Article 1.
3. **Sensitive data is a hard boundary.** Any change touching what the project
   declares sensitive runs the Gauntlet before it is called done. Article 0
   says how a project declares it; article 11 says it is automatic.
4. **Report honestly.** Article 10.
5. **The Captain dispatches; the Captain implements.** Article 11.
6. **Nothing a user enters is ever lost.** Text is never truncated, overwritten
   or dropped by a field change, a migration, a form, a view or a deploy. Any
   change that can lose data goes past the Purser before it is called done,
   whether or not the data is sensitive. Article 6 is the rule; article 11
   says it is automatic; article 12 says it is not overridable by convenience.
7. **Nothing big is built unaligned.** Work too big for one passage is
   charted first: the developer is grilled in rounds of questions with
   recommended answers, the domain's words are written into a `CONTEXT.md`
   glossary, and the work is cut into legs that each fit one passage. The
   chart lives in `docs/chart/` in the project. Article 11 carries the rule
   and the round format; article 5 carries the glossary.

---

## 2. The crew

| Agent | Called for | Writes files | Memory | Model |
|---|---|---|---|---|
| **quartermaster** | Planning and architecture, before code exists; grilling and charting when the work is bigger than one passage | No | project | inherit |
| **carpenter** | Complexity and duplication in code that exists | No | project | sonnet |
| **gunner** | Tests — permissions, ownership, isolation | Tests only | — | inherit |
| **surgeon** | Diagnosing a failure before anything is changed; builds the red loop first | No | — | inherit |
| **bosun** | Templates, CSS, UI and UX | No | — | sonnet |
| **lookout** | End-to-end QA as a real user, via the test client, and the build checked against the plan | No | — | inherit |
| **master-at-arms** | Security, GDPR, sensitive data, deploy safety | No | project | inherit |
| **purser** | Data loss — migrations, field changes, forms, deploys | No | project | inherit |

Two splits matter. **Quartermaster designs what does not exist yet; Carpenter
repairs what does.** If both seem to apply, the work is two passages, not one.
**Master-at-Arms keeps data from getting out; Purser keeps data from getting
lost.** Same record, opposite risks, different triggers: the Purser fires on
any migration, field change, text-handling form or deploy script, sensitive or
not.

Every agent preloads the `ships-articles` skill through the `skills`
frontmatter field. Subagents do not inherit the main session's skills, so this
is the only way they see the standard. Do not restate an article inside an
agent; reference it by number.

Every finding is rated on the one scale in article 11 (Critical, High,
Medium, Low), so the Captain's "fix every Critical and High" means the same
thing from every agent. An agent that invents its own words for severity
breaks that rule.

The four agents that judge against history (Quartermaster, Carpenter,
Master-at-Arms, Purser) carry `memory: project`: a directory under
`.claude/agent-memory/crew-<agent>/` in the consuming project (bare
`<agent>` on the junction route, where agents carry no plugin prefix), read before they
start and written when they finish, so a settled decision is not re-raised
and a checked pattern is not re-derived. Memory switches on Write and Edit
for the agent, which is why `guard_edit` confines those tools to the memory
directory. The Gunner, Lookout, Surgeon and Bosun stay stateless on purpose:
a walkthrough or a diagnosis should not be steered by what was true last
time.

The hooks in `plugins/crew/hooks/` enforce what the definitions say. Each is
a small Python script fed the hook's JSON on stdin; `crew-hook.sh` finds the
interpreter and runs it.

| Hook | Event | Acts on | Does |
|---|---|---|---|
| `guard-git.py` | PreToolUse Bash | gunner | Blocks `git checkout`, `restore`, `stash`, `reset`, `clean`, `switch`, which cannot tell the Gunner's mutation from the developer's uncommitted work |
| `guard_db.py` | PreToolUse Bash | every agent but the Gunner | Blocks `migrate`, `flush`, `loaddata`, `dbshell`, `--fake` and deleting the database file. The read-only commands stay allowed |
| `guard_edit.py` | PreToolUse Write, Edit | every agent but the Gunner | Refuses any edit outside `.claude/agent-memory/`. Memory switches those tools on; this keeps them pointed at memory |
| `guard_tree.py` | SubagentStart, SubagentStop | gunner, lookout | Snapshots the tree when the agent starts and refuses to let it finish while the Lookout has changed anything or the Gunner has changed a non-test file or left a `.bak`. Gives up after two refusals so the agent can report instead |
| `template_leaks.py` | PostToolUse Edit, Write | main session and agents | Reports a `{# #}`, `{{ }}` or `{% %}` opened on one line and closed on another the moment it is written. Article 7 |
| `before_stop.py` | Stop | main session | Before the turn ends: a changed `models.py` has its migration, and no changed template leaks. Article 6 and 7. Allows when already continuing, so it can never trap the developer |

Guards fail closed: no Python, no tool call. Checks fail open: nothing the
hook cannot establish ever blocks the main session from stopping.

They are wired twice because the two install routes differ: the plugin route
reads `hooks/hooks.json`, and the junction route reads the `hooks` block in
each agent's frontmatter (plugin installs ignore that block). The junction
route cannot run the two main-session hooks on its own; the README gives the
`settings.json` lines for them.

---

## 3. The Captain

`/captain <task>` is the entry point. The Captain reads the project, reads what
the project `CLAUDE.md` declares sensitive, classifies the task into one
passage — **Chart**, **Build**, **Fix**, **Tidy**, **Look** or **Ship** —
dispatches the crew that passage needs, and reports one outcome.

**Chart** is the passage for a new app or anything else that will not fit one
Build. Its shape is borrowed from Matt Pocock's wayfinder and grilling skills
(github.com/mattpocock/skills), cut down to fit a solo Django developer: no
issue tracker, no labels, the map is a markdown file in the project. The
Quartermaster sails twice on a chart, once in grilling mode to return the
first round of questions and once to draw the chart, which is the only place
the once-per-passage rule bends. Rounds are not councils: they come before
the plan, and the single council still comes after it. Each leg of a chart is
then an ordinary Build passage, and the Captain updates the chart when the
leg makes port. The Captain speaks in
nautical and piratical phrases by design; `commands/captain.md` carries the
phrase book and the two rules that keep the colour from hiding the facts.

Efficiency rules the Captain holds to:

- Independent reviewers dispatch in parallel, in one message.
- Each agent is dispatched once per passage, with every question it needs up
  front. The Gauntlet's questions ride along in the passage's own dispatches;
  it never re-runs an agent on the same files. The Chart passage's second
  Quartermaster dispatch is the one written exception.
- Questions go to the user in rounds, in the article 11 format, never one at
  a time. A round ends the turn.
- Stages that do not apply are skipped, and the skip is named in the report.
- One user checkpoint per passage — after the plan, not after every stage.
- Agents get file paths and a specific question, never "review the changes".
- No agent is spawned for something answerable in thirty seconds.

---

## 4. Skills

Skills are procedures that load themselves when the situation calls for them.
Commands are typed. That is the whole distinction.

| Skill | Loads when |
|---|---|
| **ships-articles** | Any Django work begins — the house rules, the crew rules, the round format, the glossary rule, and precedence |
| **gauntlet** | A change touches sensitive data, before it is called done — with a Purser stage when the change can lose it |

A skill description is a trigger condition, not a summary. Write it as the
situation it fires in.

---

## 5. Commands

| Command | Does |
|---|---|
| `/captain` | Takes a task, plans the passage, dispatches the crew; charts work too big for one passage and sails it a leg at a time |
| `/wheels-up` | Pre-deploy check for Django on Azure |
| `/commit-message` | Draft a structured commit message |
| `/field-report` | An agent missed something in a real project: write it up as a pattern, with nothing from the project in it, and file it as an issue for the evals |

All carry `disable-model-invocation: true` — they fire when typed, never on
their own. Generic prompts (think harder, ask me questions, dry run, explain
first, blast radius) were removed: plan mode, extended thinking and the
Quartermaster's one-question rule already cover them, and they were not Django.
The grilling that a Chart passage does is the exception that earned its
place: it is the alignment step for a whole app, it runs inside the Captain,
and it produces a glossary and a chart the rest of the crew reads.

---

## 6. Evals

`plugins/crew/evals/` is the crew's proving ground. It holds a small Django
fixture (`_fixture/schoolapp/`) with one seeded defect per agent, and a case
for each that grades whether the agent named the defect. The suite ships with
the plugin so consuming projects can run it, but its purpose is here: run it
after any change to an agent, a skill or the Articles, and read the delta
against the no-plugin baseline before deciding the change helped.

```
cd plugins/crew
claude plugin eval . --scaffold --trust-plugin --allow-tools Bash Write Edit
```

`evals/README.md` explains the fixture, the graders and how to add a case.
The one rule: never write a case for a defect you have not reproduced by hand
in the fixture first. `tools/fixture_check.py` is that reproduction, kept:
it runs every seeded defect against the fixture and fails if one has gone.

Every version that changes an agent, a skill, the Articles or the Captain
gets a row in `evals/SCORES.md`: crew score and baseline score per case.
The results directory is not committed; the scoreboard is the only record
of whether a change helped, and a rule that says "a change that lowers a
score is not an improvement" is only a rule while the previous score exists.

---

## 7. How the crew improves

The crew gets better in exactly one way: a miss becomes a case, and the case
drives the fix. Nothing else is trusted, because nothing else is measured.

**A field report.** When an agent misses something in a real project, or
says something wrong, the developer types `/field-report` there, while it
is fresh. The Captain's log ends with that reminder on every passage. The
command writes the miss up as a pattern in fixture terms, never with
anything from the project in it, and files it as an issue on this repo
labelled `field-report`. Those issues are the inbox. When `gh` is not
available in the project the report is printed instead; save it as the
next numbered file in `docs/field-reports/` so it is not lost, and work it
the same way. Working one is never an edit to the agent first. In order:

1. Seed the miss in `evals/_fixture/schoolapp/` and reproduce it by hand.
   Add the reproduction to `tools/fixture_check.py` so it is kept.
2. Write the case and run it. It should fail. If it passes, the agent did
   not miss it and the report was about routing or wording; fix that.
3. Now change the agent, the smallest change that turns the case green.
4. Run the whole suite, not just the new case, and record the row.

This is the same discipline the fixture already demands of a new case,
pointed at production misses. The agents' `memory: project` directories
stay in the consuming project on purpose; a lesson that should reach every
project comes home this way, as a case, not as memory.

**Word budgets.** Every agent, command and skill has a word budget in
`tools/budgets.json`, set at the size the file had when the budget was
introduced. `python3 tools/budget.py` fails on any overrun, and CI runs it
on every push. The budget exists because the natural fix for a miss is a
paragraph telling the agent not to miss it again, and a file that grows a
paragraph per miss becomes a list of past mistakes the model reads before
every task, with the rule that matters diluted by the fifty that do not.
So:

- Adding words means cutting words. Reread the file for what is stale,
  duplicated or already said by an Article, and remove that first.
- A budget is raised only when a case fails without the extra words and no
  shorter edit makes it pass. Note the case in the commit message.
- Cutting a file and watching the score hold is a legitimate experiment.
  Words the suite does not miss were not doing anything.

**Baselines.** The delta against plain Claude is the number to watch, and
it will shrink as the underlying model improves, because the model learns
to do on its own what an agent once had to be told. That is not the crew
getting worse. It is a signal to cut: an instruction the baseline already
follows can go. A model upgrade is a reason to re-run the suite and reread
every file with the budget in mind, not a reason to add.

---

## 8. Maintaining this file

- An agent is worth having only if it has a job no other agent has. When two
  agents overlap, merge them.
- Descriptions are what Claude matches on. Write them as trigger phrases and
  situations, not job titles, and keep each agent's phrases distinct from every
  other agent's.
- Bump `version` in `plugins/crew/.claude-plugin/plugin.json` on any change,
  then run `/plugin marketplace update crew` in consuming projects. That is the
  only version number; the marketplace manifest does not carry one.
- Test a hook change before committing: `python3 plugins/crew/hooks/selftest.py`
  feeds every hook the inputs it must act on and the ones it must let through.
  Run it with an interpreter that has Django to cover the migration check.
  CI (`.github/workflows/checks.yml`) runs it, the budget check and the
  fixture check on every push.
- Keep the roster small. Eight agents that are each obviously the right call
  beat fifteen that overlap.
- Run the evals (section 6) after changing an agent, a skill or the Articles,
  and record the row in `evals/SCORES.md` with the version bump. A change
  that lowers a case score is not an improvement, whatever it reads like.
  Run it on a laptop logged in to Claude Code, where it bills the
  subscription. `.github/workflows/evals.yml` runs it from the Actions tab
  by hand only, against an `ANTHROPIC_API_KEY` secret that bills per token:
  about 2 to 4 dollars per crew-arm run, so one case at one run per arm,
  not the suite, unless the money is deliberate.
- Stay within budget (section 7). `python3 tools/budget.py` before a commit
  that touches an agent, a command or a skill.
