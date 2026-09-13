---
description: Routing check. "It saved but came back shorter" is the Purser's trigger phrase, not the Surgeon's.
expected_outcome: The Purser is dispatched and the cause is traced to Observation.body being a CharField(max_length=200).
tags: [purser, trigger, data-loss]
runs: 3
max_turns: 30
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Agent, TaskCreate, TaskUpdate, TaskList, TaskGet]
---

A teacher says she wrote a long observation about a pupil yesterday, it saved fine, but when she opened it this morning the text came back shorter than what she typed. What's going on? Don't change anything yet.
