---
name: ships-articles
description: >-
  The house rules for writing Django in this developer projects — the standards
  every change is held to. Load at the start of any Django work: writing or
  editing a view, model, form, queryset, template, migration or settings file,
  reviewing Django code, or deciding how to structure an app. Covers what data
  counts as sensitive, permission patterns, the rule that nothing a user
  enters is ever lost, where business logic belongs, query hygiene, template
  conventions, migration safety, deployment constraints for Django on Azure,
  how the crew works together, and which instruction wins when two conflict.
---

# The Ship's Articles

Every crew signs the articles. These are the standards this developer holds
Django work to. Follow them without being asked; say so when a task requires
breaking one.

The crew's agents carry these articles preloaded. A rule written here is the
rule; the agents do not restate it.

## 0. What the data is

Assume every project holds sensitive personal data until the project says
otherwise. In this developer's projects that is usually Article 9 special
category data about children in care: names, emotional states, observed
behaviours, safeguarding context. A permissions defect here is a notifiable
data breach and the end of the client relationship, not a bug report.

The project `CLAUDE.md` declares what is sensitive with two lines:

```
Sensitive apps: tolerance, sdq, flashcards, evaluation
Sensitive models: Observation, WeeklyMap, SDQResponse
```

If the project declares nothing, those values are the defaults. Any model that
links to a declared model is in scope too. If you are not sure whether
something is in scope, it is.

## 1. Permissions are filtered, not hidden

The single most important rule.

- Every queryset returning user-owned or sensitive data filters by the
  logged-in user or their school. Not the template. Not a hidden button.
- `Model.objects.all()` in a view is wrong until proven otherwise.
- `get_object_or_404(Model, pk=pk)` without an ownership filter is a defect.
  Write `get_object_or_404(Model, pk=pk, owner=request.user)` or filter the
  queryset first.
- Assume every PK in a URL will be edited by hand by someone who should not see
  the record. Design for that, and test for it.
- Every sensitive object carries a link to its school or organisation, and every
  access path goes through that link.
- Permissions are enforced in views, querysets and forms. A check that lives
  only in a template is an architectural failure, not a detail.
- No sensitive data in URLs, logs, error messages, redirects, admin list
  displays, or any payload sent to an external API.

## 2. Boring Django beats clever Django

Prefer the built-in. `LoginRequiredMixin` over manual session handling.
`django.contrib.auth` over custom auth. The ORM over raw SQL. Function-based
views where they are clearer — do not force class-based views for symmetry.

Do not introduce a third-party package where the Django built-in is adequate.
Do not introduce an abstraction until the third repetition. Do not turn a small
app into enterprise architecture.

## 3. Logic has one home

- Field validation → forms, or model `clean()`
- Permission filtering → custom QuerySets and managers
- Object behaviour → model methods
- Cross-model workflow → a service function
- Display formatting → templates and template filters

A view that does permission checks, form processing, complex queries, business
rules, dashboard maths and email is doing five jobs too many. The goal is not a
`services.py` in every app — it is that a rule lives in exactly one place.

## 4. Query hygiene

- No queries inside loops.
- `select_related` for foreign keys, `prefetch_related` for reverse and M2M
  relations, wherever a template iterates.
- Filter in the database, never load everything and filter in Python.
- Paginate anything that can grow unbounded.
- Annotate for counts rather than counting in the template.

Do not optimise beyond this speculatively. Fix obvious risk; leave the rest.

## 5. Models describe the real workflow

Name models after what they are in the domain, not what they are in the
database. Prefer several clear models over one generic one with a `type` field.
Add `created_at` and `updated_at` by default. Give every model a useful
`__str__`. Index the fields that are actually filtered on. Use `choices` rather
than free text where the set is known. Avoid nullable fields unless null
genuinely means something different from empty. Every new field on a sensitive
model has a stated, minimal purpose; collection without one is a GDPR finding.

## 6. Nothing written is ever lost

After article 1, the rule the users would name first. What a person types is
evidence about a child. It cannot be re-written from memory. Losing it is a
failure of the one promise the software makes.

Migrations are one-way:

- Never edit a migration that has been applied anywhere but this machine.
- Review the generated migration before running it. A rename Django reads as a
  drop-and-add will lose data. A migration that removes, renames, retypes or
  shrinks a column is destructive until a data migration and a confirmed
  backup say otherwise.
- Run `python manage.py makemigrations --check --dry-run` before declaring work
  finished.
- Data migrations are separate from schema migrations, and are reversible or
  explicitly marked as not. A `RunPython` body never slices, strips or
  defaults over existing text.

Fields, forms and views keep what they are given:

- Free text is a `TextField`. A `CharField` with a guessed `max_length` for
  anything typed in sentences is a defect. SQLite in development ignores
  `max_length`; Postgres on Azure enforces it, and the user loses what they
  wrote.
- An edit form renders the full stored value. Never `truncatechars`,
  `truncatewords`, `striptags` or a `maxlength` attribute on a field the user
  will save back. Save, reload, re-save: identical.
- Views never assign `request.POST.get("field", "")` to a model, never
  `update_or_create` over a row the user did not mean to replace, and never
  `save()` an instance loaded with `.only()` or `.defer()`.
- An invalid form re-renders bound, with everything the user typed still in
  it. The session outlasts the longest form.
- No `on_delete=CASCADE` from a pupil, school or user towards observations,
  responses or notes without a stated retention decision. Deleting a parent
  never silently deletes a child's history.
- Emoji, accents, curly quotes and Windows line endings survive save and
  display unchanged.

Any change that adds or alters a migration, changes a model field, edits a
form or template handling stored text, or touches a deploy script goes past
the **purser** before it is called done. That is automatic, not requested.

## 7. Templates

A base template, and partials for anything repeated. `{% include %}` before a
custom template tag; a custom tag before repeating the block a third time.
Minimal logic in templates — no deeply nested conditionals, no business rules.
Consistent naming and page structure across apps.

## 8. Tests earn their place

Test what can actually go wrong: ownership, permissions, cross-user isolation,
form validation, the core workflow, and any model method with real logic. Do not
test field labels, page titles or CSS classes. Name the test after the failure
it catches: `test_user_cannot_access_another_users_observation`, not
`test_403`. Use Django `TestCase`, `self.client` for views, and the real
database. No pytest or external frameworks unless the project already uses
them.

## 9. Deployment: Django on Azure

- `SECRET_KEY` from an environment variable. Never in the repo.
- `DEBUG` defaults to `False` when the env var is absent.
- `ALLOWED_HOSTS` handles `WEBSITE_HOSTNAME` and is never a wildcard in
  production.
- `CSRF_TRUSTED_ORIGINS` set; secure cookie and HSTS settings on.
- WhiteNoise in `INSTALLED_APPS` and `MIDDLEWARE` for static files.
- Postgres in production, not SQLite.
- Password validators on, sensible session expiry, no custom crypto.
- **No Windows-only packages in `requirements.txt`** — `pywin32`, `winreg` and
  friends will break the Linux build. Development is on Windows; deployment is
  not.

## 10. Honest reporting

Run the tests. Report the real result. If something fails, say so with the
output. If a step was skipped, say which and why. Never describe work as
verified when it was only read. Reading code and running a flow are different
claims; label which one you made.

## 11. How the crew works

- The Captain dispatches and the Captain implements. Agents plan, review,
  diagnose and test; the main session writes the code. The Gunner is the one
  agent that writes files, and it writes only tests.
- Agents do not spawn agents.
- Each agent is dispatched once per set of files per passage. It gets the file
  paths and every question it needs in that one dispatch, including the
  Gauntlet's questions when the change is in scope under article 0. It is not
  sent back for a second look at the same files.
- Any change in scope under article 0 runs the Gauntlet before it is called
  done. That is automatic, not requested.
- Any change that adds or alters a migration, changes a model field, edits a
  form or template handling stored text, or touches a deploy script goes past
  the Purser before it is called done, whether or not it is in scope under
  article 0. Also automatic.

## 12. Precedence

When instructions conflict, later wins over earlier:

1. These articles and the agent definitions.
2. The project `CLAUDE.md` of the app the crew is working in.
3. The developer's instructions in the current session.

Three things are not overridable by convenience: the Gauntlet on sensitive
data (article 0), the Purser on anything that can lose data (article 6), and
honest reporting (article 10). If the developer asks to skip the Gauntlet or
the Purser, say plainly that it is a data-protection gate, then do as they
decide, and record in the report that it was skipped at their instruction.
