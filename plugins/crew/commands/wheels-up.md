---
name: wheels-up
description: "Wheels Up: the pre-deploy check before pushing a Django app to Azure"
disable-model-invocation: true
---

# Wheels Up — Pre-Deploy

The pre-deploy check before pushing to Azure. Work through each stage in order.
Stop and surface any failure before continuing.

---

## Stage 1 — Final tidy

Dispatch the **carpenter** agent on the files changed since the last commit. Ask
for anything obviously messy — oversized views, duplicated logic, or code that
will be painful to debug in production. Fix every High finding before moving on.

If the changes touch pupil data, permissions, auth, `settings.py` or an external
API, dispatch **master-at-arms** in parallel with the Carpenter. Do not deploy
past an unresolved Critical or High finding.

---

## Stage 2 — Deployment checklist

Check each item and report a clear pass or fail. Do not infer a pass — read the
file or run the command.

1. **requirements.txt** — no Windows-only packages (`pywin32`, `winreg` and
   similar) that would break the Linux Azure build.
2. **SECRET_KEY** — read from an environment variable in `settings.py`, not
   hardcoded.
3. **DEBUG** — defaults to `False` when no env var is set.
4. **Migrations** — `python manage.py migrate --check` reports nothing
   outstanding, and `python manage.py makemigrations --check --dry-run` reports
   no unmade migrations.
5. **Static files** — WhiteNoise present in both `INSTALLED_APPS` and
   `MIDDLEWARE`.
6. **ALLOWED_HOSTS** — not empty, not a wildcard, and handles the
   `WEBSITE_HOSTNAME` environment variable.
7. **Tests** — `python manage.py test` passes. Report the actual counts.
8. **Open TODOs** — grep the project for `TODO`, `FIXME` and `HACK` and list
   anything in the changed files.
9. **Secrets** — no `.env`, key, token or password committed in this change.

---

## Stage 3 — Commit message

When the checklist passes, confirm the user wants to commit, then draft a commit
message in the project style: present tense, concise, focused on why rather than
what.

Do not push. Pushing is the user decision.

---

## Verdict

**Ready to deploy** or **Fix before deploying**, with every failure listed. One
line each. If a check could not be run, say so — an unrun check is not a pass.
