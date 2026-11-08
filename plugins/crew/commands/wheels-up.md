---
name: wheels-up
description: "Wheels Up: the pre-deploy check before pushing a Django app to Azure"
disable-model-invocation: true
---

# Wheels Up — Pre-Deploy

The pre-deploy check before pushing to Azure. Work through each stage in order.
Stop and surface any failure before continuing. Read `docs/crew-log.md` first
for the Admiralty items still open; an open one blocks the deploy until the
developer has decided it.

---

## Stage 1 — Security and the Purser's count

Dispatch in one message:

- **master-at-arms** on the files changed since the last deploy, if any of
  them touch pupil data, permissions, auth, `settings.py`, an external API or
  a model call. Do not deploy past an unresolved Critical or High.
- **purser** on every migration not yet applied in production, every model
  field changed since the last deploy, every form or template handling stored
  text that changed, and the startup command or pipeline that runs
  `migrate`. Give it the file paths. Ask it to confirm, by number:
  1. No migration removes, renames, retypes or shrinks a column without a
     data migration that preserves the contents.
  2. No `AddField` on a live table drops its database default.
  3. No `RunPython` body slices, strips, re-encodes or defaults over existing
     text.
  4. Every edit form renders the full stored value and re-renders bound on
     validation error.
  5. No `flush`, `loaddata`, `--fake` or reset in the deploy path.

If the Purser finds any migration destructive, the verdict is **Fix before
deploying** until a backup is confirmed and its pre-migrate checklist has been
followed. That is not a judgement call.

---

## Stage 2 — Deployment checklist

Check each item and report a clear pass or fail. Read the file or run the
command; never infer a pass.

1. **requirements.txt**: no Windows-only packages.
2. **SECRET_KEY**: from an environment variable, not hardcoded.
3. **DEBUG**: defaults to `False` when no env var is set.
4. **Migrations**: `migrate --check` reports nothing outstanding and
   `makemigrations --check --dry-run` reports nothing unmade. This proves the
   migrations exist and apply; whether they lose data is Stage 1.
5. **Backup**: if Stage 1 named a destructive migration, a production backup
   taken after the last deploy exists and the developer has confirmed it.
   Asked and answered, not inferred.
6. **Static files**: WhiteNoise in both `INSTALLED_APPS` and `MIDDLEWARE`.
7. **ALLOWED_HOSTS**: not empty, not a wildcard, handles `WEBSITE_HOSTNAME`.
8. **Tests**: `python manage.py test` passes. Report the actual counts.
9. **Open TODOs**: grep the changed files for `TODO`, `FIXME` and `HACK`.
10. **Secrets**: no `.env`, key, token or password committed in this change.
11. **AI features** (article 13), where the app calls a model: the prompt
    version string changed if the prompt did, the question set was re-run,
    and the spend cap is set.

---

## Stage 3 — Commit message

When the checklist passes, confirm the user wants to commit, then draft a
commit message in the project style: present tense, concise, focused on why.

Do not push. Pushing is the user's decision and a matter for the Admiralty.

---

## Verdict

**Ready to deploy** or **Fix before deploying**, with every failure listed, one
line each. If a check could not be run, say so: an unrun check is not a pass.
Append a crew-log entry for the Ship passage.
