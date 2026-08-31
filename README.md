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

| Agent | Called for | Was |
|---|---|---|
| **quartermaster** | Planning and architecture, before code exists | Theo + Ada |
| **carpenter** | Complexity and duplication in code that exists | Les |
| **gunner** | Tests — permissions, ownership, data isolation | Tess |
| **surgeon** | Diagnosing a failure before anything is changed | new |
| **bosun** | Templates, CSS, UI and UX | Stella |
| **lookout** | End-to-end QA as a real user | Vera |
| **master-at-arms** | Security, GDPR, pupil data, deploy safety | Victor |

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

In any project:

```
/plugin marketplace add philchurch77/crew
/plugin install crew@crew
```

Or straight from disk, no GitHub needed:

```
/plugin marketplace add "c:/Users/philc/OneDrive/Desktop/VS Code/crew"
/plugin install crew@crew
```

To enable it automatically for a project, add to that project
`.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "crew": { "source": { "source": "github", "repo": "philchurch77/crew" } }
  },
  "enabledPlugins": { "crew@crew": true }
}
```

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
