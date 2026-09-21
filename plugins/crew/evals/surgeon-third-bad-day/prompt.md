---
description: The dashboard rates Priya Nair high on three dysregulated observations; her teacher says two. The view reads as correct. Its "last four weeks" is observed_on__gte=today - 4 weeks, a 29-day window, and the seeded data has a dysregulated observation dated exactly 28 days ago. Nothing in any one file shows it; only running the dashboard against the data does. Asked through /crew:captain, whose Fix passage starts with the Surgeon. The Surgeon must build a red loop, find the boundary record, name at least one alternative it ruled out, and change nothing.
expected_outcome: A reproduction run through manage.py that shows the count of three and finds the observation dated 28 days ago; the cause traced to the dashboard's date window in tolerance/views.py including the boundary day; at least one alternative (a duplicate row, a wrong mood, the threshold) named as ruled out; no file in the project changed.
tags: [surgeon, diagnosis, red-loop, wrong-data]
runs: 3
max_turns: 50
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Agent, Bash, Write, Edit, TaskCreate, TaskUpdate, TaskList, TaskGet]
---

/crew:captain The dashboard has Priya Nair as "high" and the needs-attention email went out naming her. Mary Okafor, her teacher, is adamant Priya has had two dysregulated days in the last four weeks, not three, and she keeps her own notes so I believe her. The dev database has the school's data in it already (seed_demo has been run). Find out why the dashboard disagrees with her before we change anything. Use the project's own virtualenv at .venv if one exists. Don't edit any code, I just want the diagnosis.
