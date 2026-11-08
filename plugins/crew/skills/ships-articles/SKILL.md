---
name: ships-articles
description: >-
  The house rules for writing Django in this developer's education projects.
  Load at the start of any Django work: writing or editing a view, model,
  form, queryset, template, migration or settings file, reviewing Django
  code, or deciding how to structure an app. Covers what data counts as
  sensitive, permission patterns, the rule that nothing a user enters is ever
  lost, where logic belongs, query hygiene, templates and the design
  standard, tests, deployment on Azure, honest reporting, how the crew works,
  AI features grounded in educational documents, and which instruction wins
  when two conflict.
---

# The Ship's Articles

These are the standards this developer holds Django work to. Follow them
without being asked; say so when a task requires breaking one.

## 0. What the data is

Assume every project holds sensitive personal data until the project says
otherwise. In this developer's projects that is usually Article 9 special
category data about children in care: names, emotional states, observed
behaviours, safeguarding context. A permissions defect here is a notifiable
data breach and the end of the client relationship, not a bug report.

The project `CLAUDE.md` or `AGENTS.md` declares what is sensitive with two lines:

```
Sensitive apps: tolerance, sdq, flashcards, evaluation
Sensitive models: Observation, WeeklyMap, SDQResponse
```

If the project declares nothing, those values are the defaults. Any model that
links to a declared model is in scope too, and so is any code in a declared
app whatever its own data holds. If in doubt, it is in scope.

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
- A JSON or fetch endpoint refuses a signed-out caller with a 401 or 403 JSON
  body, never a redirect. A browser follows the redirect to a 200 login page
  and a script reads that as success. Every such endpoint is checked
  signed-out, and every client treats a redirect or a non-JSON reply as a
  failed call.
- A change that alters who may enter an area lists every entry and exit of
  that area, sign-in, sign-out, links in and links out, and says where each
  one leads for each role.

## 2. Boring Django beats clever Django

Prefer the built-in. `LoginRequiredMixin` over manual session handling.
`django.contrib.auth` over custom auth. The ORM over raw SQL. Function-based
views where they are clearer. Do not introduce a third-party package where the
built-in is adequate, an abstraction before the third repetition, or
enterprise architecture into a small app.

## 3. Logic has one home

- Field validation → forms, or model `clean()`
- Permission filtering → custom QuerySets and managers
- Object behaviour → model methods
- Cross-model workflow → a service function
- Display formatting → templates and template filters

A view that does permission checks, form processing, complex queries, business
rules, dashboard maths and email is doing five jobs too many. The goal is not a
`services.py` in every app; it is that a rule lives in exactly one place.

## 4. Query hygiene

- No queries inside loops.
- `select_related` for foreign keys, `prefetch_related` for reverse and M2M
  relations, wherever a template iterates.
- Filter in the database, never load everything and filter in Python.
- Paginate anything that can grow unbounded.
- Annotate for counts rather than counting in the template.

Do not optimise beyond this speculatively.

The accuracy rules that sit beside query hygiene, because they break the same
way, silently and later:

- `timezone.now()`, never `datetime.now()`. `USE_TZ` is on and a naive
  datetime is a bug waiting for October.
- A service function that writes to more than one row runs inside
  `transaction.atomic()`.
- A counter or total is updated with an `F()` expression, not read, added
  to and saved.
- `exists()` to ask whether; `count()` only when the number is shown.
- `get()` on a queryset that can match twice is a 500 in production. Filter
  on a unique constraint or use `first()` and handle `None`.
- Uniqueness is a `UniqueConstraint` in `Meta.constraints`, and every FK
  carries a `related_name`.
- A model saved from anywhere but a `ModelForm` calls `full_clean()` first.
- A date window is tested at both edges. "Four weeks" is 28 days, and a
  record dated exactly on the boundary is in or out by decision, not by
  accident.

## 5. Models describe the real workflow

Name models after what they are in the domain, not what they are in the
database. Prefer several clear models over one generic one with a `type` field.
Add `created_at` and `updated_at` by default. Give every model a useful
`__str__`. Index the fields that are actually filtered on. Use `choices` rather
than free text where the set is known. Avoid nullable fields unless null
genuinely means something different from empty. Every new field on a sensitive
model has a stated, minimal purpose; collection without one is a GDPR finding.

The domain has a language, and the code speaks it. A project may carry a
`CONTEXT.md` at its root: a glossary of the domain's terms, one line each,
and nothing else. Where it exists, models, fields, views, URLs, templates and
test names use its terms exactly; a term the code uses that the glossary does
not have, or uses differently, is a finding. The Captain writes the glossary
during a Chart passage and keeps it current. A glossary is never a spec.

## 6. Nothing written is ever lost

After article 1, the rule the users would name first. What a person types is
evidence about a child. It cannot be re-written from memory.

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
- `AddField` with a default and `preserve_default=False` leaves the column
  `NOT NULL` with no database default on Postgres, so the previous release's
  inserts fail during the deploy window. On a live table, keep the default
  or add the column nullable first.

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
  it. The session outlasts the longest form. An autosave counts as saved only
  on a reply that says so.
- No `on_delete=CASCADE` from a pupil, school or user towards observations,
  responses or notes without a stated retention decision.
- Emoji, accents, curly quotes and Windows line endings survive save and
  display unchanged.

Any change that adds or alters a migration, changes a model field, edits a
form or template handling stored text, or touches a deploy script goes past
the **purser** before it is called done. That is automatic.

## 7. Templates and the design standard

A base template, and partials for anything repeated. `{% include %}` before a
custom template tag; a custom tag before repeating the block a third time.
Minimal logic in templates. Consistent naming and page structure across apps.

**Nothing meant for the developer reaches the page.** Django's `{# ... #}` is
single-line only; split it across a newline and it renders as visible text,
which a teacher reads as an error message. A one-line note is `{# ... #}` on
one line; anything longer is `{% comment %} ... {% endcomment %}`. Never
`<!-- -->` for developer notes: invisible on screen, delivered to every
browser. The crew's hooks catch a split construct as it is written and again
before the turn ends; every project also carries a static test that fails on
a `{#` with no `#}` on the same line in any `*.html`.

**Who uses this software.** Unless the project says otherwise: teachers,
school leaders, SEND leads, safeguarding staff, trust and local authority
staff. They have four minutes between lessons, a poor school network, and no
tolerance for friction. Design for interruption.

**What a page is held to:**

- One obvious primary action per screen; the one thing that matters findable
  in two seconds.
- A consistent spacing scale, restrained palette, strong type hierarchy, soft
  depth over heavy borders. Calm and professional, never dated, boxy, noisy,
  childish or a database table pasted onto a page.
- Tables scannable, aligned and paginated. Forms grouped, labelled, errors
  beside the field. Every data-changing action confirms; errors say what to
  do; anything slow shows a state.
- Helpful empty states. Two similar screens look and behave the same.
- Accessible: contrast, visible focus, hit targets, semantic markup, labels
  bound to inputs. Colour is never the only signal.
- Nothing on screen the user does not need right now.
- Plain HTML and CSS unless a dependency is genuinely better.

## 8. Tests earn their place

The Captain writes the tests, in this order of priority:

1. Ownership and access: a user cannot read or write records that are not
   theirs, by any route, including a guessed PK and every filter parameter.
2. Permission enforcement at the view layer, logged out, as the wrong user,
   as the right user. A JSON endpoint answers a signed-out caller with 401 or
   403, never 302.
3. Nothing is lost: a long value with newlines, accents, curly quotes and
   emoji survives save, reload, the rendered edit form and an unchanged
   re-save byte for byte; an invalid submit keeps what was typed.
4. Form validation rejects invalid, missing or tampered input server-side.
5. Model methods and managers with real logic; the core workflow's database
   state.

Django `TestCase`, `self.client`, the real database, no new framework. Name
the test after the failure it catches. Do not test labels, titles or CSS. A
test asserts the behaviour these articles require, never the behaviour
observed: when the two differ the test is written red and the defect is
reported, not pinned as expected. Characters that matter are written as
escapes, never raw. About fifteen well-chosen tests beat fifty.

**Proof, not opinion.** A permission test is proven by breaking the control
in a copy: remove the filter, run the test, see it fail, restore the file and
confirm it byte-identical. The report names each control, the test that went
red, and that the file is restored. Reading the test is not that proof.

## 9. Deployment: Django on Azure

- `SECRET_KEY` from an environment variable. Never in the repo.
- `DEBUG` defaults to `False` when the env var is absent.
- `ALLOWED_HOSTS` handles `WEBSITE_HOSTNAME` and is never a wildcard in
  production.
- `CSRF_TRUSTED_ORIGINS` set; secure cookie and HSTS settings on.
- WhiteNoise in `INSTALLED_APPS` and `MIDDLEWARE` for static files.
- Postgres in production, not SQLite.
- Password validators on, sensible session expiry, no custom crypto.
- No Windows-only packages in `requirements.txt`. Development is on Windows;
  deployment is not.
- The deploy branch and what is live on it are facts, read with `git fetch`
  before a plan assumes them.

## 10. Honest reporting

Run the tests. Report the real result. If something fails, say so with the
output. If a step was skipped, say which and why. Reading code and running a
flow are different claims: every finding from every agent carries the label
**ran** or **read**, and a report never presents the second as the first. A
recommendation that rests on a fact nobody has checked says so in the same
sentence.

## 11. How the crew works

- The Captain dispatches, the Captain implements, the Captain writes the
  tests. Agents plan, review, diagnose and walk; they report and never edit.
  An agent with a memory directory writes there and nowhere else, and records
  patterns, decisions and file paths, never a person's name or anything a
  record holds. Agents do not spawn agents.
- Each agent is dispatched once per set of files per passage, with the file
  paths, the diff, the symptom as the user reported it with the whole
  surface in scope, every question it must answer including the Gauntlet's,
  what it may run, and what the Captain already knows. It is not sent back
  for a second look at the same files.
- An agent runs only the commands and files its dispatch names or it wrote.
  Anything else in a shared scratch directory is another agent's: read it,
  never run it. Probe files are removed before the report.
- Any change in scope under article 0 runs the Gauntlet before it is called
  done. Any change that can lose data goes past the Purser. Both automatic.
  The Captain decides scope from the files and models touched, and that
  decision is not re-opened by an agent or inherited from a chart.
- Every finding is rated on one scale, so "fix every Critical and High"
  means one thing whoever says it:
  - **Critical**: data can be exposed or lost, or the workflow does not
    work. The task is not done until it is fixed.
  - **High**: the user will hit it, or an article is broken. Fixed in this
    passage.
  - **Medium**: friction, risk or debt. Fixed unless there is a stated
    reason not to, and the reason goes in the log.
  - **Low**: polish. Noted, not required.
- The crew remembers the project in `docs/crew-log.md`: one entry per
  passage, written by the Captain when the passage makes port and read
  before the next begins. It holds the date and passage, the files touched,
  the decisions taken and why, what each agent passed as clean, and the
  Admiralty items still open. A defect found later in a file an earlier
  entry passed as clean is a probable miss, and the log says so.
- Work too big for one passage is charted before it is built: a chart in
  `docs/chart/<name>.md` names the destination, the decisions, the legs and
  the fog. Each leg is one passage and a vertical slice, demoable on its own.
- A question for the developer is asked in a round: the whole frontier,
  numbered, each with a title, the choices, and the asker's recommended
  answer, so a round can be accepted in a word. Facts are never questions;
  anything the code or a command can answer is read. A recommendation that
  depends on an unverified fact is marked and held until a step has checked
  it. The format:

  ```
  **Q1 — <title>.** <the question, with the choices if there are any>
  → Recommended: <the answer you would give, and why in one line>
  ```

## 12. Precedence

When instructions conflict, later wins over earlier:

1. These articles and the agent definitions.
2. The project `CLAUDE.md` or `AGENTS.md`.
3. The developer's instructions in the current session.

Three things are not overridable by convenience: the Gauntlet on sensitive
data (article 0), the Purser on anything that can lose data (article 6), and
honest reporting (article 10). If the developer asks to skip the Gauntlet or
the Purser, say plainly that it is a data-protection gate, then do as they
decide, and record in the report that it was skipped at their instruction.

## 13. AI features

These projects increasingly call a model over educational documents
(statutory guidance, the SEND code of practice, a school's own policies) and
over pupil data. The rules that keep that safe:

- **No identifying pupil data leaves the system.** A payload carries an
  opaque id or nothing: names, dates of birth and free text about a child are
  removed or pseudonymised before the call, and the Master-at-Arms reads the
  payload as it is built, not the variable names.
- **Every answer is grounded in a named source.** The document corpus is
  versioned and each passage carries its document and section; an answer
  cites what it drew on, and one that cites nothing is shown as the model's
  opinion, never as guidance.
- **Model output never writes to a record on its own.** A suggestion is
  shown, a person accepts or edits it, the saved text is theirs, and the
  record says it was model-assisted.
- **Every call is logged**: model, prompt version, corpus version, tokens,
  who, when. The pupil text sent is kept only under a stated retention rule.
  Prompts live in code under version control, with a version string.
- **Prompts and corpus changes are tested like code**: a fixed set of
  questions with expected answers, re-run when the prompt, the model or the
  corpus changes, before it ships.
- **The model is a dependency.** A timeout, a refusal or a failed call leaves
  the user's work intact (article 6), is shown plainly, and never retries in
  a loop. Spend is capped per school.
