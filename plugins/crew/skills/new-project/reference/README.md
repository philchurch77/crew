# Reference: a project's first commit

A Django project that boots, signs someone in and passes its tests, with
nothing of its own yet.

```
manage.py  requirements.txt  .env.example  gitignore  CLAUDE.md
config/    settings.py  deploy.py  urls.py  wsgi.py  asgi.py
core/      middleware.py (the CSP header)  context_processors.py (the names)
           testing.py (fast password hasher in tests)  tests.py (the standing tests)
accounts/  urls.py  throttle.py  tests.py  templates/accounts/ (sign in,
           locked out, change password, changed)
templates/ home.html  403.html  403_csrf.html  404.html  500.html
```

`layout.html`, the form partials, the style guide and everything under
`static/` come from the `house-style` skill's reference, copied on top.

## Steps

```bash
cp -r <new-project>/reference/. myproject/        # this folder
cp -r <house-style>/reference/static myproject/static
cp -r <house-style>/reference/templates/. myproject/templates/
cd myproject && mv gitignore .gitignore && cp .env.example .env
pip install -r requirements.txt
python manage.py migrate
python manage.py test                              # 34 tests, all green
python manage.py createsuperuser
python manage.py runserver                         # then /styleguide/
```

Set `PRODUCT_NAME` and `CLIENT_NAME` in `.env`, the brand block in
`static/css/tokens.css`, and the favicon's fill in `static/img/favicon.svg`.

## Things that look odd and are deliberate

- **`product_name`, not `site_name`.** Django's own sign-in view puts a
  `site_name` in the context, which would show the server's address in the
  top bar. A test pins it.
- **`core.middleware` and not `django-csp`.** It is twenty lines and shaped
  like Django 6.0's `SECURE_CSP`, so upgrading swaps the class for Django's.
- **`force_login` in tests, real POSTs in the sign-in tests.** With the
  throttle's backend first, `client.login()` raises; the sign-in tests post
  the form because that is the path an attacker takes.
- **URL names are not namespaced** (`home`, `login`, `logout`,
  `password_change`): `layout.html` names them.
- **SQLite locally, Postgres when `POSTGRES_HOST` is set.** A deployed site
  must set it.

## When the project grows

| Adding | Do |
|---|---|
| An app with records | `for_user()` on the queryset; ownership tests beside the views |
| A public page | Add its URL name to `EveryRouteNeedsSignInTests.PUBLIC_NAMES`, on purpose |
| A file upload | Design it with the Purser, then delete `NoStoredUploadsTests` in that change |
| Email | Then, and only then, mount password reset |
| An assistant | The `ai-features` skill's chat reference |
