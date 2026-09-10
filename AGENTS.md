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

---

## 2. The crew

| Agent | Called for | Writes files | Model |
|---|---|---|---|
| **quartermaster** | Planning and architecture, before code exists | No | inherit |
| **carpenter** | Complexity and duplication in code that exists | No | sonnet |
| **gunner** | Tests — permissions, ownership, isolation | Tests only | inherit |
| **surgeon** | Diagnosing a failure before anything is changed | No | inherit |
| **bosun** | Templates, CSS, UI and UX | No | sonnet |
| **lookout** | End-to-end QA as a real user, via the test client | No | inherit |
| **master-at-arms** | Security, GDPR, sensitive data, deploy safety | No | inherit |
| **purser** | Data loss — migrations, field changes, forms, deploys | No | inherit |

Two splits matter. **Quartermaster designs what does not exist yet; Carpenter
repairs what does.** If both seem to apply, the work is two passages, not one.
**Master-at-Arms keeps data from getting out; Purser keeps data from getting
lost.** Same record, opposite risks, different triggers: the Purser fires on
any migration, field change, text-handling form or deploy script, sensitive or
not.

Quartermaster, Carpenter, Gunner, Lookout, Master-at-Arms and Purser preload the
`ships-articles` skill through the `skills` frontmatter field. Subagents do not
inherit the main session's skills, so this is the only way they see the
standard. Do not restate an article inside an agent; reference it by number.

The Gunner is the one agent with a hook. `hooks/guard-git.py` blocks `git
checkout`, `restore`, `stash`, `reset`, `clean` and `switch` inside the gunner
subagent only. It is wired twice because the two install routes differ: the
plugin route reads `hooks/hooks.json`, and the junction route reads the
`hooks` block in the Gunner's frontmatter (plugin installs ignore that block).

---

## 3. The Captain

`/captain <task>` is the entry point. The Captain reads the project, reads what
the project `CLAUDE.md` declares sensitive, classifies the task into one
passage — **Build**, **Fix**, **Tidy**, **Look** or **Ship** — dispatches the
crew that passage needs, and reports one outcome. The Captain speaks in
nautical and piratical phrases by design; `commands/captain.md` carries the
phrase book and the two rules that keep the colour from hiding the facts.

Efficiency rules the Captain holds to:

- Independent reviewers dispatch in parallel, in one message.
- Each agent is dispatched once per passage, with every question it needs up
  front. The Gauntlet's questions ride along in the passage's own dispatches;
  it never re-runs an agent on the same files.
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
| **ships-articles** | Any Django work begins — the house rules, the crew rules, and precedence |
| **gauntlet** | A change touches sensitive data, before it is called done — with a Purser stage when the change can lose it |

A skill description is a trigger condition, not a summary. Write it as the
situation it fires in.

---

## 5. Commands

| Command | Does |
|---|---|
| `/captain` | Takes a task, plans the passage, dispatches the crew |
| `/wheels-up` | Pre-deploy check for Django on Azure |
| `/commit-message` | Draft a structured commit message |

All carry `disable-model-invocation: true` — they fire when typed, never on
their own. Generic prompts (think harder, ask me questions, dry run, explain
first, blast radius) were removed: plan mode, extended thinking and the
Quartermaster's one-question rule already cover them, and they were not Django.

---

## 6. Maintaining this file

- An agent is worth having only if it has a job no other agent has. When two
  agents overlap, merge them.
- Descriptions are what Claude matches on. Write them as trigger phrases and
  situations, not job titles, and keep each agent's phrases distinct from every
  other agent's.
- Bump `version` in `plugins/crew/.claude-plugin/plugin.json` on any change,
  then run `/plugin marketplace update crew` in consuming projects. That is the
  only version number; the marketplace manifest does not carry one.
- Test a hook change with sample input before committing:
  `echo '{"agent_type":"gunner","tool_name":"Bash","tool_input":{"command":"git stash"}}' | python3 plugins/crew/hooks/guard-git.py`
  should exit 2.
- Keep the roster small. Eight agents that are each obviously the right call
  beat fifteen that overlap.
