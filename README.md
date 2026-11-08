A Django crew for Claude Code: five specialist agents, a Captain who
dispatches them and does the building, and the house rules they all work to.
It is built for this developer's education projects, where the data is about
children, the deploy target is Azure, and the apps increasingly call a model
over educational documents. It will work in any Django project once you tell
it what is sensitive.

## Install

The crew is a Claude Code plugin. It installs the same way from the CLI,
the VS Code extension and the desktop app, and it updates in place.

**From the CLI**

```
/plugin marketplace add philchurch77/crew
/plugin install crew@crew
```

**From VS Code:** type `/plugins` in the chat panel, open the Marketplaces
tab, add `philchurch77/crew`, then install `crew`. Choose "for you" so every
project on the machine gets it.

**Pin it to a project**, so a fresh clone or a cloud session is prompted to
install it, by adding to the project's `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "crew": { "source": { "source": "github", "repo": "philchurch77/crew" } }
  },
  "enabledPlugins": { "crew@crew": true }
}
```

**Update** with `/plugin marketplace update crew`, or turn on auto-update
for the marketplace on the Marketplaces tab. A new version applies after
`/reload-plugins` or a new session.

**Check the hooks are live.** In a project with a Django `manage.py`, type:

```
Use the lookout agent to run `python manage.py loaddata nonexistent.json` and paste back exactly what it reports.
```

The Lookout should report a refusal naming `[crew hook: guard_db]` and no
output. If it reports Django's "no fixture named" error instead, the command
reached Django and the hooks are not loaded. The phrasing matters: a bare
question gets answered by the main session, which has no guards.

## Tell it what is sensitive

The crew treats every project as holding sensitive personal data. Declare which
apps and models in the project `CLAUDE.md` or `AGENTS.md`:

```
Sensitive apps: tolerance, sdq, flashcards, evaluation
Sensitive models: Observation, WeeklyMap, SDQResponse
```

Those are also the defaults when a project declares nothing. Any change that
touches a declared app or model, or anything linked to one, runs the Gauntlet
before the Captain calls it done. Separately, any change that adds or alters a
migration, changes a model field, edits a form or template that handles
stored text, or touches a deploy script goes past the Purser, sensitive or
not. Nothing a user enters is ever lost.

## The Captain

`/crew:captain <task>` is the entry point. The Captain reads the project and
what is live on the deploy branch, reads the crew log, decides whether the
Gauntlet applies, classifies the task into one passage (Chart, Build, Fix,
Tidy, Look or Ship), shows you the plan once, builds it, writes the tests,
dispatches the reviewers, and reports.

What the Captain decides alone, and what it never decides, is written down
in its own section 2. The short version: it runs the passage; you decide
anything that skips a data-protection gate, destroys data, deploys, changes
the plan's purpose, or accepts a Critical. Those come first in every log
under **Admiralty**. The log also carries **Departures**, anything done
differently from the plan you agreed, and **Probable misses**, any defect
found in a file the crew had earlier passed as clean.

## Charting something big

A single feature is a Build passage: `/crew:captain add an agreed-action
field to observations`. A whole app is not. Hand the Captain something that
will not fit one passage and it chooses the **Chart** passage: the
Quartermaster reads the project and returns a round of numbered questions,
each with a recommended answer, about the things only you can decide. Answer
a round in a word or argue with it. When nothing is left assumed, the
Quartermaster draws the chart: the destination, the decisions, the legs
(vertical slices that each fit one passage), the fog, and what is out of
scope. On your aye the Captain writes `docs/chart/<name>.md` and a
`CONTEXT.md` glossary at the project root. Then it is one leg per passage:
`/crew:captain sail leg 1 of the attendance chart`.

## What the crew remembers

Two things, both in the project, both worth committing.

**The crew log**, `docs/crew-log.md`: one entry per passage, written by the
Captain when it makes port and read before the next begins. Files touched,
decisions and why, what each agent passed as clean, Admiralty items still
open. It is how the Captain stops re-asking settled questions and how it
notices its own misses.

**Agent memory**, `.claude/agent-memory/crew-<agent>/` for the
Quartermaster, Master-at-Arms and Purser: the app boundaries, which queryset
does the filtering, which migrations have been read, which cascades you
accepted with a retention rule. Patterns, decisions and file paths, never a
person's name or anything a record holds, and the crew is told so.

## When the crew gets it wrong

Type `/crew:field-report` in that project while it is fresh. It writes the
miss up as a pattern, with nothing from your project in it, and files it as
an issue on this repo. Each report earns one line in the Articles, an agent
or the Captain, paid for by cutting a line elsewhere, so the crew gets more
precise without getting longer. AGENTS.md section 6 has the rule.

## Layout

```
AGENTS.md                         the maintainer's guide — not shipped
CLAUDE.md                         one line, imports AGENTS.md
.claude-plugin/marketplace.json   the catalogue Claude Code reads
plugins/crew/
  .claude-plugin/plugin.json      this plugin manifest, and the only version number
  agents/                         one .md per agent
  commands/                       one .md per slash command
  skills/<name>/SKILL.md          self-loading procedures — the rules live here
  hooks/                          hooks.json, the guards and checks, and their self-test
tools/                            maintainer checks — the word budgets; not shipped
.github/                          CI: checks on every push; the field-report issue template
```

## What the hooks enforce

The agents' rules are written in their definitions; the hooks make them so.

- **No agent edits your code.** Every agent is refused any Write or Edit
  outside its own memory directory. Findings come back in the report for the
  Captain to apply.
- **No agent writes to the database.** `migrate`, `flush`, `loaddata`,
  `dbshell`, `--fake` and deleting the database file are refused inside every
  agent. `showmigrations`, `sqlmigrate` and `makemigrations --check
  --dry-run` still run.
- **The Lookout leaves the tree as it found it.** It is refused permission to
  finish while the tree says otherwise, and told which files to put back.
  After two refusals it may finish and say so in its report instead.
- **A leaked template comment is caught as it is written.** A `{# #}`,
  `{{ }}` or `{% %}` split across lines is reported straight back after the
  edit, and again before the turn ends if one arrived by another route.
- **A model change has its migration before the turn ends.** If a
  `models.py` changed and `makemigrations --check --dry-run` reports one
  unmade, the turn does not end until it exists.

`python3 plugins/crew/hooks/selftest.py` exercises all of them.

## Adding to it

- **Agent**: a `.md` in `agents/` with `name` and `description` frontmatter.
  The description is what Claude matches on: trigger phrases and situations,
  distinct from every other agent's. Add `skills: [ships-articles]`. Guards
  go in `hooks/hooks.json`; plugin agents ignore a `hooks` block in their own
  frontmatter. Only add one if it has a job no existing agent has.
- **Command**: a `.md` in `commands/`. Keep `disable-model-invocation: true`.
- **Skill**: `skills/<name>/SKILL.md`, with the description written as the
  situation it fires in.

Bump `version` in `plugins/crew/.claude-plugin/plugin.json` after any change.
How the crew operates, and why it is shaped this way, is in
[AGENTS.md](AGENTS.md).
