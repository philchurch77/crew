---
name: ships-articles
description: >-
  The house rules for writing Django in this developer projects — the standards
  every change is held to. Load at the start of any Django work: writing or
  editing a view, model, form, queryset, template, migration or settings file,
  reviewing Django code, or deciding how to structure an app. Covers permission
  patterns, where business logic belongs, query hygiene, template conventions,
  migration safety and deployment constraints for Django on Azure.
---

# The Ship's Articles

Every crew signs the articles. These are the standards this developer holds
Django work to. Follow them without being asked; say so when a task requires
breaking one.

## 1. Permissions are filtered, not hidden

The single most important rule.

- Every queryset returning user-owned or pupil-linked data filters by the
  logged-in user or their school. Not the template. Not a hidden button.
- `Model.objects.all()` in a view is wrong until proven otherwise.
- `get_object_or_404(Model, pk=pk)` without an ownership filter is a defect.
  Write `get_object_or_404(Model, pk=pk, owner=request.user)` or filter the
  queryset first.
- Assume every PK in a URL will be edited by hand by someone who should not see
  the record. Design for that, and test for it.
- Every sensitive object carries a link to its school or organisation, and every
  access path goes through that link.

## 2. Boring Django beats clever Django

Prefer the built-in. `LoginRequiredMixin` over manual session handling.
`django.contrib.auth` over custom auth. The ORM over raw SQL. Function-based
views where they are clearer — do not force class-based views for symmetry.

Do not introduce a third-party package where the Django built-in is adequate.
Do not introduce an abstraction until the third repetition.

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
genuinely means something different from empty.

## 6. Migrations are one-way

- Never edit a migration that has been applied anywhere but this machine.
- Review the generated migration before running it. A rename Django reads as a
  drop-and-add will lose data.
- Run `python manage.py makemigrations --check --dry-run` before declaring work
  finished.
- Data migrations are separate from schema migrations, and are reversible or
  explicitly marked as not.

## 7. Templates

A base template, and partials for anything repeated. `{% include %}` before a
custom template tag; a custom tag before repeating the block a third time.
Minimal logic in templates — no deeply nested conditionals, no business rules.
Consistent naming and page structure across apps.

## 8. Tests earn their place

Test what can actually go wrong: ownership, permissions, cross-user isolation,
form validation, the core workflow, and any model method with real logic. Do not
test field labels, page titles or CSS classes. Name the test after the failure
it catches. Use Django `TestCase` and the real database.

## 9. Deployment: Django on Azure

- `SECRET_KEY` from an environment variable. Never in the repo.
- `DEBUG` defaults to `False` when the env var is absent.
- `ALLOWED_HOSTS` handles `WEBSITE_HOSTNAME` and is never a wildcard in
  production.
- WhiteNoise in `INSTALLED_APPS` and `MIDDLEWARE` for static files.
- Postgres in production, not SQLite.
- **No Windows-only packages in `requirements.txt`** — `pywin32`, `winreg` and
  friends will break the Linux build. Development is on Windows; deployment is
  not.

## 10. Honest reporting

Run the tests. Report the real result. If something fails, say so with the
output. If a step was skipped, say which and why. Never describe work as
verified when it was only read.
