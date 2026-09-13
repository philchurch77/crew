---
description: Migration 0002 alters Observation.body from TextField to CharField(max_length=200); Observation.pupil cascades from Pupil.
expected_outcome: Says 0002 will truncate or reject stored observations and must not run as is; also flags the CASCADE from pupil to observations.
tags: [purser, migrations, data-loss]
runs: 3
max_turns: 30
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Agent, TaskCreate, TaskUpdate, TaskList, TaskGet]
---

I'm about to deploy the tolerance app to Azure and there's a new migration, tolerance/migrations/0002_shorten_body.py, that hasn't run in production yet. Production has about 4,000 observations in it already. Is this migration safe to run? Check the model changes behind it too. Don't change anything, just tell me.
