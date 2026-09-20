---
description: Every page raises RelatedObjectDoesNotExist for a user with no Membership row, because _school_for reads user.membership unguarded. Reported as "the dashboard gives a 500 for one new user", through /crew:captain, whose Fix passage starts with the Surgeon. The Surgeon must build a red loop, name the real cause, and change nothing.
expected_outcome: A reproduction run through manage.py that shows the error; the cause traced to _school_for in tolerance/views.py and the missing Membership for the user, with the observation that it is not specific to the dashboard; no file in the project changed.
tags: [surgeon, diagnosis, red-loop]
runs: 3
max_turns: 50
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Agent, Bash, Write, Edit, TaskCreate, TaskUpdate, TaskList, TaskGet]
---

/crew:captain The dashboard gives a 500 for our new deputy head but works fine for every other teacher. Her user account was created yesterday in the admin. Find out why before we change anything. Use the project's own virtualenv at .venv if one exists. Don't edit any code, I just want the diagnosis.
