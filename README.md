<img width="3200" height="2484" alt="crew" src="https://github.com/user-attachments/assets/6027489e-8edb-41e3-852b-1f60391bd619" />


A Django crew for Claude Code: eight specialist agents, a Captain who dispatches
them, and the house rules they work to. It is built for this developer's
education projects, where the data is about children and the deploy target is
Azure. It will work in any Django project once you tell it what is sensitive.

## Install

Which route you use depends on whether you have the Claude Code CLI. The VS Code
extension on its own does **not** ship the plugin manager — `/plugin` reports
that it is not available in this environment.

### With the CLI — as a plugin

```
/plugin marketplace add philchurch77/crew
/plugin install crew@crew
```

To pin it to a specific project, add to that project `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "crew": { "source": { "source": "github", "repo": "philchurch77/crew" } }
  },
  "enabledPlugins": { "crew@crew": true }
}
```

### Without the CLI — junctions (Windows)

Clone the repo somewhere stable, outside any synced folder, then point the
user-level Claude Code directories at it. Junctions do not need admin rights.

> This replaces your user-level `agents`, `commands`, `skills` and `hooks`
> directories. If any of them already exist with your own files, move those
> files into the clone first, or the junction will fail to create.

```powershell
git clone https://github.com/philchurch77/crew.git "$env:USERPROFILE\dev\crew"

$src = "$env:USERPROFILE\dev\crew\plugins\crew"
foreach ($d in @("agents","commands","skills","hooks")) {
  New-Item -ItemType Junction -Path "$env:USERPROFILE\.claude\$d" -Target "$src\$d"
}
```

Claude Code reads `~/.claude/agents`, `~/.claude/commands` and `~/.claude/skills`
in every project, so the crew is then available everywhere. The `hooks` junction
lets the agents' guards find their scripts. Restart Claude Code once after
creating the junctions.

If the `hooks` junction is missing, every Bash command the guarded agents run
is refused before it starts, with a message naming this section. That is a
guard failing loud rather than silently switching itself off; create the
junction and restart.

Two hooks run in the main session rather than inside an agent, and the
junction route cannot wire those from an agent file. To get them, add to
`~/.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      { "matcher": "Edit|Write|MultiEdit", "hooks": [
        { "type": "command", "command": "sh \"$HOME/.claude/hooks/crew-hook.sh\" template_leaks" } ] }
    ],
    "Stop": [
      { "hooks": [
        { "type": "command", "command": "sh \"$HOME/.claude/hooks/crew-hook.sh\" before_stop", "timeout": 150 } ] }
    ]
  }
}
```

Updating is just:

```powershell
git -C "$env:USERPROFILE\dev\crew" pull
```

The change is live in every project immediately — nothing to copy.

On macOS or Linux use symlinks instead:

```sh
git clone https://github.com/philchurch77/crew.git ~/dev/crew
for d in agents commands skills hooks; do
  ln -s ~/dev/crew/plugins/crew/$d ~/.claude/$d
done
```

Both routes serve the same files. The junction route ignores the plugin
manifests and `hooks/hooks.json`; the agents' guards still run there through
the `hooks` block in their own frontmatter.

## Tell it what is sensitive

The crew treats every project as holding sensitive personal data. Declare which
apps and models in the project `CLAUDE.md`:

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

## What the crew remembers

Quartermaster, Carpenter, Master-at-Arms and Purser keep notes on each
project in `.claude/agent-memory/crew-<agent>/` inside that project (the
junction route drops the `crew-` prefix): the app
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
  evals/                          the proving ground: a seeded fixture and one case per agent
```

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
