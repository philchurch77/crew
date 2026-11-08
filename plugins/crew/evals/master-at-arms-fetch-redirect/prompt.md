---
description: The observation edit page autosaves through fetch to observation_autosave, which is behind @login_required. A signed-out POST gets a 302 to the login page; fetch follows it to a 200 HTML page, autosave.js reads response.ok as a save, shows "Saved" and drops the unsaved-text warning, and the text is lost. Reading the decorator says the endpoint refuses anonymous callers; only asking what a signed-out request receives finds it. Asked through /crew:captain as a Look; field reports 17 and 30.
expected_outcome: A finding, rated Critical or High, that a signed-out autosave is redirected to the login page, which fetch follows to a 200 that autosave.js treats as saved, so typed text is lost while the page says Saved; fix is a 401 or 403 JSON response from the endpoint and/or the script treating a redirect or non-JSON reply as a failed save.
tags: [master-at-arms, lookout, purser, gauntlet, data-loss]
runs: 3
max_turns: 60
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Agent, Bash, Write, Edit, TaskCreate, TaskUpdate, TaskList, TaskGet]
---

/crew:captain I've added autosave to the observation edit page (`tolerance/static/tolerance/autosave.js` posting to `observation_autosave` in `tolerance/views.py`) because teachers were losing long notes when a tab closed. Before it goes to the school, look it over: is it secure, and is there any way a teacher can still lose what they've typed? Use the project's own virtualenv at .venv if one exists. Don't change any code, just report.
