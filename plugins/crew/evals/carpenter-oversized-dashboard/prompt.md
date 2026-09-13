---
description: The dashboard view runs four queries per pupil in a loop and mixes business rules, sorting and email into one function.
expected_outcome: Names the per-pupil queries in the loop and the business rules in the view, and points to annotate/aggregate and a model or service home for the rules.
tags: [carpenter, complexity, query-hygiene]
runs: 3
max_turns: 30
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Agent, TaskCreate, TaskUpdate, TaskList, TaskGet]
---

The dashboard view in tolerance/views.py has grown and it's getting messy. It's also slow on the school with 300 pupils. Can you review it for complexity and tell me what to simplify? Don't refactor it, just give me the findings.
