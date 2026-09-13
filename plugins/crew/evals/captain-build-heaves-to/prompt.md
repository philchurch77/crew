---
description: The Captain, handed a feature, must read the water, name the passage, send the Quartermaster aloft, show the plan and stop. No code before the council.
expected_outcome: A Build passage is named, the Gauntlet and the Purser are both declared to apply, the Quartermaster is dispatched, a plan is shown, and the run ends waiting for the user with no file edited.
tags: [captain, build, routing]
runs: 3
max_turns: 40
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Agent, TaskCreate, TaskUpdate, TaskList, TaskGet]
---

/crew:captain add an "agreed action" field to observations in the tolerance app, so that when a teacher records an observation she can also write down what was agreed with the safeguarding lead as a result. It needs to show on the detail page and be editable on the form.
