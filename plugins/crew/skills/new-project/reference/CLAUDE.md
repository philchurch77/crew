# CLAUDE.md

Standing rules only. History lives in git.

## What this is

**PRODUCT**, for **CLIENT**: one sentence on who uses it and for what.

Apps: `accounts` (sign-in; accounts made in the admin), `core` (the
security header, the standing tests). Add each app here as it arrives, in
a line.

    Sensitive apps:
    Sensitive models:

Fill those two lines in before the first model is written (article 0).
Until they are filled in, everything is in scope.

## Rules that keep it working

- **Filter by user at the queryset**: `Model.objects.for_user(user)`.
  `objects.all()` in a view is a defect.
- **No inline `<script>`, `on*=`, `style=` or `<style>` in a template**: the
  CSP blocks them. Settings reach JS through `data-` attributes or
  `json_script`.
- **Never log what a person typed.**
- **Pages are built from the house style** (`static/css/components.css`,
  `/styleguide/`): tokens only, components before new CSS.
- **Every route is private unless listed** in
  `core.tests.EveryRouteNeedsSignInTests`.
- **Comments are brief**: why, not what; no history.

## Verifying

```bash
python manage.py test
python manage.py makemigrations --check --dry-run
```

Bar for handing back: tests pass, and a changed page has been looked at in
a browser at 1280 and 390 wide beside `/styleguide/`.
