---
description: The Captain, handed a whole new app, must choose the Chart passage, send the Quartermaster aloft in grilling mode, relay a round of questions with recommended answers, and stop. No plan, no chart file and no code before the developer has answered.
expected_outcome: A Chart passage is named, the Quartermaster is dispatched, the final message is a numbered round of questions each with a recommended answer about the attendance app, and the run ends waiting for the user with no file written.
tags: [captain, chart, routing]
runs: 3
max_turns: 40
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Agent, TaskCreate, TaskUpdate, TaskList, TaskGet]
---

/crew:captain chart an attendance app for schoolapp. Teachers take a register for their class twice a day, morning and afternoon, and mark each pupil present, absent or late. The office needs to see who is missing right now so they can ring parents. The head wants a weekly attendance percentage per pupil and per class. An absence can be marked as authorised afterwards when a note comes in.
