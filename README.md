# crew

A reusable Claude Code plugin: the review crew and workflow commands I use across
my Django projects. Install once, available in every project.

## What's in it

**Agents** (`plugins/crew/agents/`)

| Agent | Use it for |
|---|---|
| **Theo** | Planning a feature before any code is written |
| **Ada** | Django architecture review at design time (models, app layout) |
| **Les** | Simplifying code that already exists (fat views, duplication) |
| **Tess** | Writing tests for permissions, ownership, access control |
| **Stella** | UI/UX review of templates and CSS |
| **Vera** | End-to-end QA from a real user's perspective |
| **Victor** | Security, privacy, GDPR, deployment safety |
| **Juno** | Auditing this setup itself — gaps, overlaps, what to build next |

**Commands** (`plugins/crew/commands/`)

Workflows: `/build` (feature end-to-end), `/gauntlet` (pupil-data review),
`/wheels-up` and `/pre-deploy` (Azure pre-deploy checks).

Habits: `/think-hard`, `/grill-me`, `/dry-run`, `/explain-code`,
`/check-impact`, `/commit-message`.

## Install

Push this repo to GitHub, then in any project:

```
/plugin marketplace add philchurch/crew
/plugin install crew@crew
```

To use it straight from disk instead (no GitHub needed):

```
/plugin marketplace add "c:/Users/philc/OneDrive/Desktop/VS Code/crew"
/plugin install crew@crew
```

Enable it automatically for a project by adding to that project's
`.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "crew": { "source": { "source": "github", "repo": "philchurch/crew" } }
  },
  "enabledPlugins": { "crew@crew": true }
}
```

## Layout

```
.claude-plugin/marketplace.json   the catalogue Claude Code reads
plugins/crew/
  .claude-plugin/plugin.json      this plugin's manifest
  agents/                         one .md per agent
  commands/                       one .md per slash command
  skills/                         multi-file skills (skills/<name>/SKILL.md)
```

## Adding to it

- **Agent** — drop a `.md` in `agents/` with `name` and `description` frontmatter.
  The description is what Claude matches on, so write it as trigger phrases.
- **Command** — drop a `.md` in `commands/`. Keep
  `disable-model-invocation: true` for anything you only ever want to fire by typing `/name`.
- **Skill** — `skills/<name>/SKILL.md` plus any supporting files it references.
  Use a skill over a command when it needs bundled scripts or reference docs.

Bump `version` in `plugins/crew/.claude-plugin/plugin.json` when you change things, then
`/plugin marketplace update crew` in a consuming project to pull it.
