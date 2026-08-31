# crew

A Claude Code plugin: a Django crew, a Captain who dispatches them, and the
standards they work to. Install once, available in every project.

Hand the Captain a task and it plans the passage, dispatches the crew it needs
and reports one outcome:

```
/captain add a parent portal to the tolerance app
/captain the SDQ dashboard totals are wrong
/captain get this ready to deploy
```

## The crew

| Agent | Called for
|---|---|---|
| **quartermaster** | Planning and architecture, before code exists
| **carpenter** | Complexity and duplication in code that exists
| **gunner** | Tests — permissions, ownership, data isolation
| **surgeon** | Diagnosing a failure before anything is changed
| **bosun** | Templates, CSS, UI and UX
| **lookout** | End-to-end QA as a real user
| **master-at-arms** | Security, GDPR, pupil data, deploy safety

The split that matters: the **Quartermaster** designs what does not exist yet;
the **Carpenter** repairs what does.

## Skills

Skills load themselves when the situation calls for them. Commands are typed.

| Skill | Loads when |
|---|---|
| **ships-articles** | Any Django work begins — the house rules |
| **gauntlet** | A change touches pupil data, before it is called done |

The Gauntlet is the important one. Any change to the `tolerance`, `sdq`,
`flashcards` or `evaluation` apps triggers a Master-at-Arms audit and a Lookout
walkthrough automatically — nobody has to remember to ask.

## Commands

`/captain` · `/wheels-up` · `/think-hard` · `/grill-me` · `/dry-run` ·
`/explain-code` · `/check-impact` · `/commit-message`

## Install

Which route you use depends on whether you have the Claude Code CLI. The VS Code
extension on its own does **not** ship the plugin manager — `/plugin` reports
that it is not available in this environment.

### Without the CLI — junctions (Windows)

Clone the repo somewhere stable, outside any synced folder, then point the
user-level Claude Code directories at it. Junctions do not need admin rights.

```powershell
git clone https://github.com/philchurch77/crew.git "$env:USERPROFILE\dev\crew"

$src = "$env:USERPROFILE\dev\crew\plugins\crew"
foreach ($d in @("agents","commands","skills")) {
  New-Item -ItemType Junction -Path "$env:USERPROFILE\.claude\$d" -Target "$src\$d"
}
```

Claude Code reads `~/.claude/agents`, `~/.claude/commands` and `~/.claude/skills`
in every project, so the crew is then available everywhere. Restart Claude Code
once after creating the junctions.

Updating is just:

```powershell
git -C "$env:USERPROFILE\dev\crew" pull
```

The change is live in every project immediately — nothing to copy.

On macOS or Linux use symlinks instead:

```sh
git clone https://github.com/philchurch77/crew.git ~/dev/crew
for d in agents commands skills; do
  ln -s ~/dev/crew/plugins/crew/$d ~/.claude/$d
done
```

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

Both routes serve the same files. The junction route ignores the plugin
manifests; the plugin route uses them.

## Layout

```
AGENTS.md                         the constitution — read this first
CLAUDE.md                         one line, imports AGENTS.md
.claude-plugin/marketplace.json   the catalogue Claude Code reads
plugins/crew/
  .claude-plugin/plugin.json      this plugin manifest
  agents/                         one .md per agent
  commands/                       one .md per slash command
  skills/<name>/SKILL.md          self-loading procedures
```

## Adding to it

- **Agent** — a `.md` in `agents/` with `name` and `description` frontmatter.
  The description is what Claude matches on: write it as trigger phrases and
  situations, not a job title. Only add one if it has a job no existing agent
  has.
- **Command** — a `.md` in `commands/`. Keep `disable-model-invocation: true`
  so it fires only when typed.
- **Skill** — `skills/<name>/SKILL.md`. Use a skill when the procedure should
  load itself; write the description as the trigger condition.

Bump `version` in `plugins/crew/.claude-plugin/plugin.json` after any change,
then `/plugin marketplace update crew` in consuming projects.

Full detail on how the crew operates is in [AGENTS.md](AGENTS.md).
