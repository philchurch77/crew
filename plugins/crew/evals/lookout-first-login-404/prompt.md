---
description: settings.py has no LOGIN_REDIRECT_URL, so a teacher who logs in from the login page is sent to /accounts/profile/ and gets a 404. Every view works; only the walk from the login page finds it. The Lookout must walk the flow with the test client, report the 404, and leave the tree untouched.
expected_outcome: A walkthrough run through manage.py that POSTs the login form and follows the redirect; a finding that the post-login landing page is a 404 at /accounts/profile/, traced to the missing LOGIN_REDIRECT_URL; labelled ran, not read; no file changed.
tags: [lookout, qa, end-to-end]
runs: 3
max_turns: 60
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Agent, Bash, Write, Edit, TaskCreate, TaskUpdate, TaskList, TaskGet]
---

Before we ship this to the first school, walk the whole thing as a brand new teacher would: she gets the login page link in an email, logs in, records her first observation about a pupil, opens it, edits it, and looks at the dashboard. Tell me what's broken or confusing from her point of view. Use the project's own virtualenv at .venv if one exists. Don't fix anything.
