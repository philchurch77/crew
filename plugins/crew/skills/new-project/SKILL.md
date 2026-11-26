---
name: new-project
description: >-
  How one of this developer's Django projects starts: a reference project
  with settings, security headers, sign-in with a login throttle, error
  pages and the standing tests, ready for the house style and the first
  app. Load when the developer asks for a new project, a new app or tool
  from scratch, a prototype, a starter, a skeleton or scaffolding; when
  there is no manage.py yet; and when an existing project is missing its
  Content Security Policy, its login throttle or its standing tests.
---

# New project

Every project starts the same way, so the parts nobody should have to think
about are already right: where secrets come from, what the browser is
allowed to load, who can sign in, what a signed-out visitor can reach. The
start is a project in `reference/` that runs and passes its tests as
copied. Read `reference/README.md` for the steps; the files are the
pattern.

## What the Captain does

1. **Ask four things, once.** The product's name, the client's name, the
   client's colours, and what the data is (article 0). Everything else has
   a default.
2. **Copy `reference/`**, then the `house-style` skill's `static/` and
   `templates/` on top. Rename `gitignore` to `.gitignore`. Set the names
   in `.env`, the brand block in `tokens.css`, and run the contrast check.
3. **Write the project's `CLAUDE.md`** from `reference/CLAUDE.md`: the two
   sensitive lines first, declared before any model exists.
4. **Run it**: `migrate`, the tests, `/styleguide/` in a browser. All
   green before a line of the project's own code.
5. **Chart the first feature.** The starter is not the plan. The
   Quartermaster grills the real work as it would any other.

## What comes ready, and why it stays

- **Settings from the environment.** A missing `SECRET_KEY` refuses to
  boot; `DEBUG` on a deployed site refuses to boot; a deployed site with
  no Postgres refuses to boot. Each is a guard against a quiet mistake.
- **A Content Security Policy with nothing inline and nothing remote.** It
  is why templates carry no `<script>`, `style=` or `on*=`, and it is what
  stops anything a person typed leaving the page in a URL. Loosening it is
  the Admiralty's decision, never a fix for a blocked script.
- **Sign-in only.** Accounts are made in the admin; there is no sign-up
  and no password reset until the project has email. Five wrong passwords
  from one address pause that username there, on the admin too.
- **The admin is superusers only.**
- **No uploads.** Nothing takes a file until one is designed with the
  Purser; a test fails if a `FileField` appears before then.
- **The standing tests** (`core/tests.py`). They scan the whole project,
  so they cover apps that do not exist yet: no leaked template note,
  nothing inline, the policy on every response, and **every route private
  unless listed**. A new public page is added to that list on purpose.
  Routes that take an argument get their own ownership tests (article 8).

## The first app

- A model that belongs to someone has a `for_user()` on its queryset, and
  every view starts from it (article 1). `objects.all()` in a view is a
  defect.
- A page extends `layout.html` and is built from the house style's
  components. A form uses the two form partials.
- A JSON endpoint answers a signed-out caller 401, never a redirect.
- If the project has an assistant, the `ai-features` skill's chat
  reference is the app to copy.

## What this skill does not do

It does not deploy: `/crew:wheels-up` and article 9. It does not choose
the data model. It is not a framework to keep in step: once copied the
files are the project's, and a fix worth keeping comes back here by a
field report.
