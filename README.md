A Django crew for Claude Code: eight specialist agents, a Captain who dispatches
them, and the house rules they work to. It is built for this developer's
education projects, where the data is about children and the deploy target is
Azure. It will work in any Django project once you tell it what is sensitive.

## Install

The crew is a Claude Code plugin. It installs the same way from the CLI,
the VS Code extension and the desktop app, and it updates in place.

**From the CLI**

```
/plugin marketplace add philchurch77/crew
/plugin install crew@crew
```

**From VS Code:** type `/plugins` in the chat panel, open the Marketplaces
tab, add `philchurch77/crew`, then install `crew` for this project.

**Pin it to a project**, so anyone who opens the repo is prompted to install
it, by adding to the project's `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "crew": { "source": { "source": "github", "repo": "philchurch77/crew" } }
  },
  "enabledPlugins": { "crew@crew": true }
}
```

Cloud sessions do not see plugins installed on your laptop, so a project
that wants the crew there needs those lines too.

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
apps and models in the project `CLAUDE.md` (or `AGENTS.md`):

```
Sensitive apps: tolerance, sdq, flashcards, evaluation
Sensitive models: Observation, WeeklyMap, SDQResponse
```

Those are also the defaults when a project declares nothing. Any change that
touches a declared app or model, or anything linked to one, runs the Gauntlet
before the Captain calls it done.

Separately, any change that adds or alters a migration, changes a model field,
edits a form or template that handles stored text, or touches a deploy script
goes past the Purser, sensitive or not. Nothing a user enters is ever lost.

## Charting something big

A single feature is a Build passage: `/captain add an agreed-action field to
observations`. A whole app is not. Hand the Captain something that will not
fit one passage and it chooses the **Chart** passage instead:

```
/captain chart an attendance app: AM and PM registers per class, ...
```

The Quartermaster reads the project and comes back with a round of numbered
questions, each with a recommended answer, about the things only you can
decide: what finished looks like, what the domain's words mean, who owns
what. Answer a round in a word or argue with it. When nothing is left
assumed, the Quartermaster draws the chart: the destination, the decisions,
the legs (vertical slices that each fit one passage and each leave a user
able to do something new), the fog it can see but not yet cut, and what is
out of scope. On your aye the Captain writes two files and nothing else:
`docs/chart/<name>.md` and a `CONTEXT.md` glossary at the project root that
every agent then uses for names.

Then it is one leg per passage:

```
/captain sail leg 1 of the attendance chart
```

That is an ordinary Build passage with the chart in the Quartermaster's
hands, and the chart is updated when the leg makes port. Commit both files.

## When the crew gets it wrong

The crew improves by being measured, not by being told. If an agent misses
something or says something wrong, type `/field-report` in that project
while it is fresh (the Captain's log reminds you). It writes the miss up as
a pattern, with nothing from your project in it, and files it as an issue
here. Reports are worked in clusters: a pattern several reports share becomes
one seeded defect and one failing eval case before the agent is changed,
so the fix is proven rather than hoped. `docs/field-reports/LEDGER.md`
tracks every report from filed to fixed.

## What the crew remembers

Quartermaster, Carpenter, Master-at-Arms and Purser keep notes on each
project in `.claude/agent-memory/crew-<agent>/` inside that project: the app
boundaries, the decisions you have taken and why, which queryset does the
permission filtering, which migrations have been read, which cascades you
accepted with a stated retention rule. They read it before they start and
update it when they finish, so a settled decision is not re-raised at the next
council and a checked pattern is not re-derived.

Commit that directory. It is patterns, decisions and file paths, never a
person's name or anything a record holds, and the crew is told so. If you
would rather keep it out of the repo, change `memory: project` to
`memory: local` in the four agent files and the directory becomes
`.claude/agent-memory-local/`.

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
  evals/                          the proving ground: a seeded fixture, one case per agent, and SCORES.md
tools/                            maintainer checks — word budgets and the fixture check; not shipped
docs/field-reports/               reports that could not be filed as issues, and LEDGER.md: one row per report
.github/                          CI: checks on every push, evals by hand; the field-report issue template
```

In a project the crew works on, it reads and keeps `docs/chart/*.md` and a
root `CONTEXT.md` when work has been charted, and `.claude/agent-memory/`
for the four agents that remember.

## What the hooks enforce

The agents' rules are written in their definitions; the hooks make them so.

- **The Gunner cannot discard your work.** `git checkout`, `restore`, `stash`,
  `reset`, `clean` and `switch` are refused inside the Gunner, which mutates
  files on purpose and cannot tell its mutation from your uncommitted fix.
- **Reviewers cannot edit your code.** Every agent but the Gunner is refused
  any Write or Edit outside its own memory directory. Their findings come back
  in the report for the Captain to apply.
- **Reviewers cannot write to the database.** `migrate`, `flush`, `loaddata`,
  `dbshell`, `--fake` and deleting the database file are refused inside every
  agent but the Gunner. `showmigrations`, `sqlmigrate` and `makemigrations
  --check --dry-run` still run.
- **The Lookout leaves the tree as it found it, and the Gunner changes only
  tests.** Each is refused permission to finish while the tree says otherwise,
  and told which files to put back. After two refusals it may finish and say
  so in its report instead.
- **A leaked template comment is caught as it is written.** A `{# #}`,
  `{{ }}` or `{% %}` split across lines is reported straight back after the
  edit, and again before the turn ends if one arrived by another route.
- **A model change has its migration before the turn ends.** If a `models.py`
  changed and `makemigrations --check --dry-run` reports one unmade, the turn
  does not end until it exists.

`python3 plugins/crew/hooks/selftest.py` exercises all of them.

## Adding to it

- **Agent** — a `.md` in `agents/` with `name` and `description` frontmatter.
  Guards go in `hooks/hooks.json`; plugin agents ignore a `hooks` block in
  their own frontmatter.
  The description is what Claude matches on: write it as trigger phrases and
  situations, not a job title, and keep them distinct from the other agents.
  Add `skills: [ships-articles]` if it reviews Django code. Only add one if it
  has a job no existing agent has.
- **Command** — a `.md` in `commands/`. Keep `disable-model-invocation: true`
  so it fires only when typed. If it is not about Django, it does not belong.
- **Skill** — `skills/<name>/SKILL.md`. Use a skill when the procedure should
  load itself; write the description as the trigger condition.

Bump `version` in `plugins/crew/.claude-plugin/plugin.json` after any change,
then `/plugin marketplace update crew` in consuming projects.

How the crew operates, and why it is shaped this way, is in
[AGENTS.md](AGENTS.md).
