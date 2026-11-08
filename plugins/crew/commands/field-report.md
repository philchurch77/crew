---
name: field-report
description: "An agent missed something or got it wrong: write it up as a pattern, with nothing from this project in it, and file it on the crew repo"
argument-hint: What went wrong — e.g. "the Purser passed a migration that drops a column" or "the Captain sent the Surgeon one hypothesis"
disable-model-invocation: true
---

# Field report

One of the crew missed something, or said something wrong, and the developer
wants the crew to learn from it. A report becomes one line in the Articles,
an agent or the Captain, paid for by a cut, so the pattern has to be exact.

What went wrong, in the developer's words: **$ARGUMENTS**

If that is empty, ask what the crew got wrong and stop.

## Gather

Take it from this conversation: the Captain's log, the agent's own report,
the prompt the developer typed, and the crew log entry if the miss shows a
file passed clean that was not. Read project files only to understand the
pattern. If one thing you need is missing, ask for it in one round.

## The one rule

Nothing from this project goes in the report. No person's name, no record,
no query result, no pasted file, no client name, no URL. Describe the defect
as a pattern in generic school terms: a `School`, a `Pupil`, an
`Observation`, a teacher who records and a safeguarding lead who reads.
"The Purser passed a migration that drops `Observation.mood` without a
backup" is a report; anything naming what the real column held is not.

## Write

```
## Agent
Which agent, or the Captain's routing or dispatch if that was the fault.

## Passage
Chart, Build, Fix, Tidy, Look or Ship, and the stage.

## Prompt
What the developer typed, in generic terms.

## What the agent said
Quoted from its report, redacted to the pattern.

## What it should have said
The finding, the severity on the article 11 scale, and the fix.

## The line it needs
The one sentence, and which file it belongs in: an Article by number, an
agent, or a section of the Captain. If it cannot be said in one sentence,
say what pattern the reports would need to share before it earns more.
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
The fix is made in the crew repo, never here.
