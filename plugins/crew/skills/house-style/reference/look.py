"""See a page as a person would, beside the style guide.

    python look.py /reports/ /reports/new/            signed in as a superuser
    python look.py --anon /accounts/login/            signed out
    python look.py --setup reports.tests.sample /reports/

Run from the project root. It builds Django's TEST database, serves the
project from it, opens each path in a real browser at 1280 and 390 wide,
saves a screenshot of each (and of /styleguide/) outside the project, and
prints what it measured: console errors (a CSP block shows here), sideways
scroll, the number of h1s and primary buttons, small tap targets and
unlabelled fields. Nothing in the project or its real database is touched.

--setup names a function that creates the records the page needs; if it
returns a user, the browser signs in as them.

Needs:  pip install playwright && playwright install chromium
(LOOK_CHROMIUM names a browser binary to use instead.)
"""
import argparse
import importlib
import os
import sys
import tempfile
import unittest
from pathlib import Path

WIDTHS = (("wide", 1280, 900), ("phone", 390, 800))

MEASURE = """() => {
  const shown = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const all = (sel) => [...document.querySelectorAll(sel)].filter(shown);
  const words = (el) => (el.innerText || el.getAttribute('aria-label') || el.id || el.tagName).trim().slice(0, 40);
  return {
    sideways: document.documentElement.scrollWidth > window.innerWidth,
    h1: all('h1').length,
    primary: all('.btn--primary').map(words),
    small: all('main a, main button, main input:not([type=hidden]), main select')
      .filter((el) => { const r = el.getBoundingClientRect(); return r.height < 32 || (el.matches('button, .btn') && r.height < 44 && !el.matches('.btn--small, .chat-row__menu, .chat-menu__item')); })
      .map(words).slice(0, 8),
    unlabelled: all('main input:not([type=hidden]), main select, main textarea')
      .filter((el) => !(el.labels && el.labels.length) && !el.getAttribute('aria-label') && !el.getAttribute('aria-labelledby'))
      .map((el) => el.name || el.id || el.tagName),
    inline: document.querySelectorAll('[style]:not(textarea)').length,
  };
}"""


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("paths", nargs="+", help="paths to open, e.g. /reports/")
    parser.add_argument("--anon", action="store_true", help="do not sign in")
    parser.add_argument("--setup", help="dotted path to a function that creates records")
    parser.add_argument("--out", help="folder for screenshots (default: a new temp folder)")
    args = parser.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("look.py needs a browser:  pip install playwright && playwright install chromium")

    sys.path.insert(0, os.getcwd())
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    # So the style guide's routes exist; the server is local and temporary.
    os.environ.setdefault("DEBUG", "True")
    # Playwright's sync API runs an event loop on this thread.
    os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")
    import django
    django.setup()
    from django.conf import settings
    from django.contrib.auth import get_user_model
    from django.contrib.staticfiles.testing import StaticLiveServerTestCase
    from django.test.runner import DiscoverRunner

    out = Path(args.out or tempfile.mkdtemp(prefix="look-"))
    out.mkdir(parents=True, exist_ok=True)
    report = []

    class Look(StaticLiveServerTestCase):
        def test_look(self):
            user = None
            if args.setup:
                module, _, name = args.setup.rpartition(".")
                user = getattr(importlib.import_module(module), name)()
            if not args.anon:
                user = user or get_user_model().objects.create_superuser("lookout", password="x" * 20)
                self.client.force_login(user)

            with sync_playwright() as pw:
                binary = os.environ.get("LOOK_CHROMIUM")
                browser = pw.chromium.launch(executable_path=binary) if binary else pw.chromium.launch()
                paths = list(args.paths)
                if "/styleguide/" not in paths:
                    paths.append("/styleguide/")
                for label, width, height in WIDTHS:
                    context = browser.new_context(viewport={"width": width, "height": height})
                    if not args.anon:
                        context.add_cookies([{
                            "name": settings.SESSION_COOKIE_NAME,
                            "value": self.client.cookies[settings.SESSION_COOKIE_NAME].value,
                            "url": self.live_server_url,
                        }])
                    for path in paths:
                        page = context.new_page()
                        errors = []
                        page.on("console", lambda m, e=errors: e.append(m.text) if m.type == "error" else None)
                        page.on("pageerror", lambda exc, e=errors: e.append(str(exc)))
                        response = page.goto(self.live_server_url + path)
                        page.wait_for_load_state("networkidle")
                        # Measured first: a full-page screenshot leaves its own marks.
                        seen = page.evaluate(MEASURE)
                        shot = out / f"{path.strip('/').replace('/', '-') or 'home'}-{label}.png"
                        page.screenshot(path=str(shot), full_page=True)
                        if path != "/styleguide/" or path in args.paths:
                            report.append((path, label, response.status, seen, errors, shot))
                        page.close()
                    context.close()
                browser.close()

    runner = DiscoverRunner(verbosity=0, interactive=False)
    runner.setup_test_environment()
    databases = runner.setup_databases()
    try:
        result = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, "w")).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Look)
        )
    finally:
        runner.teardown_databases(databases)
        runner.teardown_test_environment()
    if not result.wasSuccessful():
        for _, trace in result.errors + result.failures:
            print(trace, file=sys.stderr)
        sys.exit(1)

    findings = 0
    for path, label, status, seen, errors, shot in report:
        print(f"\n{path}  [{label}]  HTTP {status}\n  screenshot: {shot}")
        notes = []
        if errors:
            notes += [f"console error: {e[:160]}" for e in errors]
        if seen["sideways"]:
            notes.append("the page scrolls sideways")
        if seen["h1"] != 1:
            notes.append(f"{seen['h1']} visible h1 (one is expected)")
        if len(seen["primary"]) > 1:
            notes.append(f"{len(seen['primary'])} primary buttons: {', '.join(seen['primary'])}")
        if seen["small"]:
            notes.append(f"small tap targets: {', '.join(seen['small'])}")
        if seen["unlabelled"]:
            notes.append(f"fields with no label: {', '.join(seen['unlabelled'])}")
        if seen["inline"]:
            notes.append(f"{seen['inline']} elements carry a style attribute")
        findings += len(notes)
        print("\n".join(f"  - {n}" for n in notes) or "  nothing measured out of line")
    print(f"\nStyle guide, to compare: {out / 'styleguide-wide.png'} and {out / 'styleguide-phone.png'}")
    print(f"{findings} thing(s) to look at. The screenshots are the review; these counts only point.")


if __name__ == "__main__":
    main()
