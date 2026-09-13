---
description: The observation detail view fetches by pk with no school filter. A security review must name it.
expected_outcome: Names observation_detail in tolerance/views.py as reachable across schools and says how to fix it.
tags: [master-at-arms, gauntlet, permissions]
runs: 3
max_turns: 30
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Agent, TaskCreate, TaskUpdate, TaskList, TaskGet]
---

This Django project records teacher observations about pupils. A trust DPO is reviewing it next week. Do a security and permissions review of the tolerance app: I need to know whether staff at one school can see another school's observations, and anything else a DPO would pick up on. Don't change any code, just report.
