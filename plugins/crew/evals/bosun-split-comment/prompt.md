---
description: A Django {# #} comment split across three lines in observation_form.html renders as visible page text.
expected_outcome: Names the split comment in tolerance/templates/tolerance/observation_form.html as the cause and gives the right syntax.
tags: [bosun, templates]
runs: 3
max_turns: 30
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Agent, TaskCreate, TaskUpdate, TaskList, TaskGet]
---

Can you review the UI of the observation form in the tolerance app? A teacher told me there was some odd text above the form when she went to add an observation, and she thought something had gone wrong. I'd like a design review of that screen too while you're in there. Don't edit anything, just tell me what you find.
