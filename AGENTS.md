# The Crew

This repository is a Claude Code plugin. It carries a crew of Django agents, a
Captain who dispatches them and builds, and the standards they all work to.
Installed into a project, the whole crew comes with it.

This file is the maintainer's guide. **It does not ship with the plugin.**
Nothing at the repo root is loaded into a project that installs the crew; only
`plugins/crew/` is. The rules the crew works to live in the `ships-articles`
skill, the Gauntlet lives in the `gauntlet` skill, and the Captain's procedure
lives in `commands/captain.md`. Edit those to change behaviour. Edit this file
to explain it.

`CLAUDE.md` imports this file so sessions in this repo read it.

---

## 1. What the crew is for

1. **The crew serves Django work in education.** Every agent assumes Django,
   a real client, sensitive data about children, and a teacher with four
   minutes between lessons, until the project says otherwise. Keep them
   specific. A generic agent is a worse agent.
2. **Permissions are filtered, never hidden.** Article 1.
3. **Sensitive data is a hard boundary.** Any change touching what the
   project declares sensitive runs the Gauntlet before it is called done.
   Article 0 says how a project declares it; article 11 says the Captain
   decides scope and it is automatic.
4. **Nothing a user enters is ever lost.** Any change that can lose data goes
   past the Purser, sensitive or not. Article 6.
5. **Report honestly, and label it.** Every finding from every agent is ran
   or read. Article 10.
6. **The Captain dispatches, implements and tests**, and is trusted to run a
   passage alone within stated decision rights. Article 11 and the Captain's
   section 2.
7. **The crew remembers the project.** A crew log per project, read before
   every passage and written after it, so settled decisions stay settled and
   a miss is noticed by the crew itself. Article 11.
8. **Nothing big is built unaligned.** Work too big for one passage is
   charted first, in rounds of questions with recommended answers, into legs
   that each fit one passage.
9. **AI features are grounded and logged.** No identifying pupil data leaves
   the system, every answer cites a source, nothing a model writes reaches a
   record without a person. Article 13 is the rule; the `ai-features`
   skill's reference app is the pattern, and its tests run against a
   throwaway project before the skill changes.

---

## 2. The crew

| Agent | Called for | Memory | Model |
|---|---|---|---|
| **quartermaster** | Planning before code exists; grilling and charting when the work is bigger than one passage; reviewing the structure of code that has grown wrong | project | inherit |
| **surgeon** | Diagnosing a failure before anything is changed; maps the surface, builds the red loop first | — | inherit |
| **lookout** | End-to-end QA as a real user through the test client, the page as the teacher sees it, and the build checked against the plan | — | inherit |
| **master-at-arms** | Security, GDPR, sensitive data, AI payloads, deploy safety | project | inherit |
| **purser** | Data loss: migrations, field changes, forms, autosaves, deploys | project | inherit |

No agent writes a file outside its memory directory. The Captain writes the
code and the tests, and proves the access-control tests by breaking the
control in a copy (article 8), which is why there is no test-writing agent:
the base model writes tests as well as a specialist did, and the proof is a
procedure, not a persona.

Two splits matter. **Quartermaster plans what does not exist and reviews what
does**, in two modes, once per passage. **Master-at-Arms keeps data from
getting out; Purser keeps data from getting lost.** Same record, opposite
risks, different triggers.

Every agent preloads the `ships-articles` skill through the `skills`
frontmatter field. Subagents do not inherit the main session's skills, so this
is the only way they see the standard. Do not restate an article inside an
agent; reference it by number. Every finding is rated on the one scale in
article 11.

The three agents that judge against history carry `memory: project`, a
directory under `.claude/agent-memory/crew-<agent>/` in the consuming
project. Memory switches on Write and Edit, which is why `guard_edit`
confines those tools to it. The Surgeon and Lookout stay stateless on
purpose: a diagnosis or a walkthrough should not be steered by what was true
last time. The crew log is the shared memory, and the Captain's.

The hooks in `plugins/crew/hooks/` enforce what the definitions say. Each is
a small Python script fed the hook's JSON on stdin; `crew-hook.sh` finds the
interpreter and runs it.

| Hook | Event | Acts on | Does |
|---|---|---|---|
| `guard_db.py` | PreToolUse Bash | every agent | Blocks `migrate`, `flush`, `loaddata`, `dbshell`, `--fake` and deleting the database file. Read-only commands stay allowed |
| `guard_edit.py` | PreToolUse Write, Edit | every agent | Refuses any edit outside `.claude/agent-memory/` |
| `guard_tree.py` | SubagentStart, SubagentStop | lookout | Snapshots the tree when the agent starts and refuses to let it finish while anything differs. Gives up after two refusals so the agent can report instead |
| `template_leaks.py` | PostToolUse Edit, Write | main session and agents | Reports a `{# #}`, `{{ }}` or `{% %}` opened on one line and closed on another the moment it is written. Article 7 |
| `before_stop.py` | Stop | main session | Before the turn ends: a changed `models.py` has its migration, and no changed template leaks. Allows when already continuing, so it can never trap the developer |

Guards fail closed: no Python, no tool call. Checks fail open: nothing the
hook cannot establish ever blocks the main session from stopping. All are
wired in `hooks/hooks.json`; a plugin agent ignores a `hooks` block in its
own frontmatter, so none carries one.

---

## 3. The Captain

`/crew:captain <task>` is the entry point. `commands/captain.md` is the one
file that makes the crew trustworthy, so its shape matters:

- **Section 1, read the water**: fetch first and state what is live; read
  the crew log; decide the Gauntlet from the files touched, finally.
- **Section 2, decision rights**: what the Captain decides alone and what is
  always the Admiralty's. One council per passage, after the plan.
- **Section 3, the passages**: Chart, Build, Fix, Tidy, Look, Ship. The
  Captain writes and proves the tests in Build and Fix.
- **Section 5, the dispatch**: the brief as the user gave it with the whole
  surface, the diff, every question, what the agent may run and write, what
  the Captain knows. Most field reports in 2026 were dispatch faults: a
  narrowed hypothesis, a contradictory order, a stale assumption about what
  was live. The template is the fix for all of them.
- **Section 6, the log and the crew log**: Admiralty first, Departures,
  Probable misses, ran or read on every finding; then the crew-log entry.

**Chart** borrows its shape from Matt Pocock's wayfinder and grilling skills
(github.com/mattpocock/skills), cut down for a solo Django developer. The
Quartermaster sails twice on a chart, the one exception to once per passage.

---

## 4. Skills and commands

Skills load themselves when the situation calls for them; commands are typed.

| Skill | Loads when |
|---|---|
| **ships-articles** | Any Django work begins |
| **gauntlet** | A change touches sensitive data, before it is called done |
| **ai-features** | A task adds or changes anything that calls a model, grounds answers in documents or sends pupil text to a model; carries a reference Django app (`reference/`) that the Captain copies from |

| Command | Does |
|---|---|
| `/crew:captain` | Takes a task, runs the passage, writes the log and the crew log |
| `/crew:wheels-up` | Pre-deploy check for Django on Azure |
| `/crew:commit-message` | Draft a structured commit message |
| `/crew:field-report` | An agent missed something: write it up as a pattern and file it |

All carry `disable-model-invocation: true`. A skill description is a trigger
condition, not a summary.

---

## 5. Checks

`.github/workflows/checks.yml` runs on every push: the hook selftest
(`python3 plugins/crew/hooks/selftest.py`, which builds its own tiny Django
project) and the word budgets (`python3 tools/budget.py`). Both take seconds
and cost nothing. There is no eval suite. One existed through 2.15; it was
dropped because a fresh fixture can never measure the thing that makes the
crew better than plain Claude on these projects, which is knowing the
project, and because its first real run showed plain Claude matching the
crew on code reading. The crew is judged on the developer's own projects:
whether the Captain stops re-asking settled questions, whether its log is
reliable, and whether it catches its own misses.

---

## 6. How the crew improves

Two ways, and only two.

**It learns the project by itself.** The crew log and the agent memories
accumulate decisions, patterns and what has been checked. This is the lever
that compounds across similar projects, and it needs no maintenance beyond
the Captain writing an honest entry.

**You correct it with one line.** When an agent misses something in a real
project, `/crew:field-report` writes the miss up as a pattern and files it
as an issue labelled `field-report`. Working one is one sentence in the
Articles, an agent or the Captain, paid for by cutting a sentence elsewhere,
then a version bump and the issue closed with the line quoted. Not a
paragraph: a file that grows a paragraph per miss becomes a list of past
mistakes the model reads before every task, with the rule that matters
diluted by the fifty that do not.

**Word budgets** make that stick. Every agent, command and skill has a
budget in `tools/budgets.json`, set at the size the file had when the budget
was set. `python3 tools/budget.py` fails on any overrun, and CI runs it on
every push. Adding words means cutting words. A budget rises only when a
report cannot be answered any shorter, and the commit says which report.

**A model upgrade is a reason to cut.** The base model learns to do on its
own what an agent once had to be told. After an upgrade, reread every file
with the budget in mind and run `/doctor prompt-audit`, which flags
instructions written for older models. Remove what it names.

---

## 7. Maintaining this file

- An agent is worth having only if it has a job no other agent has. When two
  overlap, merge them. Five is the current roster; fewer is fine.
- Descriptions are what Claude matches on. Trigger phrases and situations,
  distinct per agent.
- Bump `version` in `plugins/crew/.claude-plugin/plugin.json` on any change.
  Consuming projects update with `/plugin marketplace update crew` or
  marketplace auto-update.
- Test a hook change before committing with the selftest, under a Python
  that has Django.
- Stay within budget before any commit that touches an agent, a command or
  a skill.
