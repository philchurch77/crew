---
name: field-report
description: "An agent missed something or got it wrong: write it up as a field report for the crew's evals, with nothing from this project in it, and file it"
argument-hint: What went wrong — e.g. "the Purser passed a migration that drops a column" or "the Captain sent this to the Surgeon, it was the Purser's"
disable-model-invocation: true
---

# Field report

One of the crew missed something, or said something wrong, and the developer
wants the crew to learn from it. The crew does not learn by being told; it
learns when the miss becomes a case in the crew's eval suite, the case fails,
and the agent is changed until it passes. This command writes the report
that case will be built from.

What went wrong, in the developer's words: **$ARGUMENTS**

If that is empty, ask what the crew got wrong and stop.

## Gather

Take it from this conversation: the Captain's log, the agent's own report,
the prompt the developer typed. Read project files only to understand the
pattern. If one thing you need is not in the conversation, ask for it in one
round, then write the report.

## The one rule

Nothing from this project goes in the report. No person's name, no record,
no query result, no pasted file, no client name, no URL. Describe the
defect as a pattern in the words of the crew's fixture, a school app with
`School`, `Membership`, `Pupil` and `Observation` models, a teacher who
records observations and a safeguarding lead who reads them. "The Purser
passed a migration that drops `Observation.mood` without a backup" is a
report; anything naming what the real column held is not. If the pattern
cannot be described without project detail, say so in the report and
describe what you can.

## Write

```
## Agent
Which agent, or the Captain's routing if the wrong agent was sent.

## Passage
Chart, Build, Fix, Tidy, Look or Ship, and the stage.

## Prompt
What the developer typed, with project specifics turned into fixture terms.

## What the agent said
Quoted from its report, redacted to the pattern.

## What it should have said
The finding, the severity on the article 11 scale, and the fix.

## The defect, in fixture terms
Where in schoolapp it would be seeded and what the seed is, so it can be
reproduced by hand before a case is written.

## Grader
PASS if ... FAIL if ... in one sentence each, concrete enough for a small
judge model.
```

## File

Title it `Field report: <agent> <one line>`. Try:

```
gh issue create --repo philchurch77/crew --label field-report --title "..." --body-file <tempfile>
```

If `gh` is missing or the command fails, print the report in full in a fenced
block and give the developer this link to paste it into:
https://github.com/philchurch77/crew/issues/new?template=field-report.md&labels=field-report

Delete the temp file. Do not change the agent, the plugin or this project.
The fix is made in the crew repo, from the case, never here.
