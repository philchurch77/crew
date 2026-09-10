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
lets the Gunner's git guard find its script. Restart Claude Code once after
creating the junctions.

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
manifests and `hooks/hooks.json`; the Gunner's guard still runs there through
the `hooks` block in its own frontmatter.

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
  hooks/                          hooks.json and the Gunner's git guard
```

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
