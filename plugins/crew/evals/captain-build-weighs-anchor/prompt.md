---
description: Resumes captain-build-heaves-to after the ship's council. The user says aye; the Captain must implement, dispatch the reviewers in parallel, then the Gunner, then the Lookout, and finish with the log.
expected_outcome: The field, migration, form and templates are changed; Carpenter, Bosun, Master-at-Arms and Purser are dispatched in one message; the Gunner runs tests and the log reports the real result with Gauntlet and Purser lines.
tags: [captain, build, passage]
runs: 3
max_turns: 80
timeout_seconds: 1800
allowed_tools: [Read, Glob, Grep, Skill, Agent, Bash, Write, Edit, TaskCreate, TaskUpdate, TaskList, TaskGet]
---

Aye, the plan is sound. Bundle the permission fix and the comment fix in with it; they are in the same files and I would rather have them done. Weigh anchor. The project's virtualenv is at .venv if there is one.
