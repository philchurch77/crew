"""The standing tests: rules every page and route keeps, whoever wrote it.
They scan the whole project, so a new app is covered without being added."""
import re

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.template.loader import render_to_string
from django.test import SimpleTestCase, TestCase
from django.urls import URLPattern, URLResolver, get_resolver

from config.deploy import database_config, is_deployed, unresolved_key_vault_references

# Every folder holding templates, found rather than listed.
TEMPLATE_ROOTS = ("templates",) + tuple(sorted(
    path.parent.name for path in settings.BASE_DIR.glob("*/templates")
    if path.is_dir() and path.parent.name not in (".venv", "venv", "node_modules")
))


def scan_templates(pattern, keep=lambda match, text: True):
    """file:line of every match of ``pattern`` that ``keep(match, text)``
    accepts, in any template."""
    offenders = []
    for root in TEMPLATE_ROOTS:
        for path in sorted((settings.BASE_DIR / root).rglob("*.html")):
            text = path.read_text(encoding="utf-8")
            for match in re.finditer(pattern, text, re.IGNORECASE):
                if keep(match, text):
                    line_no = text.count("\n", 0, match.start()) + 1
                    offenders.append(f"{path.relative_to(settings.BASE_DIR)}:{line_no}")
    return offenders


class TemplateNotesTests(SimpleTestCase):
    """Article 7: nothing meant for the developer reaches the page."""

    # Catches a {# #} split across lines: it renders as visible text, which
    # staff read as an error message.
    def test_no_short_comment_spans_a_line(self):
        def unclosed(match, text):
            line_end = text.find("\n", match.start())
            return "#}" not in text[match.start():line_end if line_end != -1 else len(text)]

        offenders = scan_templates(r"\{#", unclosed)
        self.assertEqual(offenders, [], "Use {% comment %} for more than a line: " + ", ".join(offenders))

    # Catches an HTML comment: invisible on screen, delivered to every browser.
    def test_no_html_comments(self):
        offenders = scan_templates(r"<!--(?!\[if)")
        self.assertEqual(offenders, [], "Notes are {# #}, not <!-- -->: " + ", ".join(offenders))


class NothingInlineTests(SimpleTestCase):
    """The CSP blocks inline script and style silently, and the "fix" would
    be 'unsafe-inline', removing the backstop."""

    # Catches an inline <script>: its code never runs. A JSON data island
    # (json_script) is not executed and is allowed.
    def test_no_inline_script_elements(self):
        def inline(match, text):
            attrs = match.group(1)
            if re.search(r"\ssrc\s*=", attrs, re.IGNORECASE):
                return False
            return not re.search(r"\stype\s*=\s*[\"']application/json[\"']", attrs, re.IGNORECASE)

        offenders = scan_templates(r"<script\b([^>]*)>", inline)
        self.assertEqual(offenders, [], "Inline <script> at: " + ", ".join(offenders))

    # Catches onclick= and friends: the handler (a delete's confirmation,
    # say) silently never fires.
    def test_no_inline_event_handlers(self):
        offenders = scan_templates(r"<[^>]*\son[a-z]+\s*=")
        self.assertEqual(offenders, [], "Inline handlers at: " + ", ".join(offenders))

    # Catches style= and <style>, blocked by style-src.
    def test_no_inline_style(self):
        offenders = scan_templates(r"<[^>]*\sstyle\s*=") + scan_templates(r"<style\b")
        self.assertEqual(offenders, [], "Inline style at: " + ", ".join(offenders))

    # Catches href="javascript:...": inline script by another name.
    def test_no_javascript_urls(self):
        offenders = scan_templates(r"javascript\s*:")
        self.assertEqual(offenders, [], "javascript: URLs at: " + ", ".join(offenders))


class SecurityHeaderTests(TestCase):
    # Catches the policy being dropped or loosened: it is what stops typed
    # text leaving the page in a URL.
    def test_every_response_carries_a_policy_with_nothing_inline_or_remote(self):
        for path in ("/accounts/login/", "/", "/no-such-page/"):
            with self.subTest(path=path):
                policy = self.client.get(path).headers.get("Content-Security-Policy", "")
                self.assertIn("default-src 'none'", policy)
                self.assertIn("script-src 'self'", policy)
                self.assertNotIn("unsafe", policy)
                self.assertNotIn("http", policy)

    # Catches the site becoming frameable (clickjacking a signed-in user).
    def test_pages_cannot_be_framed(self):
        response = self.client.get("/accounts/login/")
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")
        self.assertIn("frame-ancestors 'none'", response.headers["Content-Security-Policy"])


def _plain_routes(patterns=None, prefix=""):
    """(path, name) for every route that takes no arguments. The admin has
    its own tests below."""
    for entry in patterns if patterns is not None else get_resolver().url_patterns:
        route = prefix + str(entry.pattern)
        if isinstance(entry, URLResolver):
            if entry.namespace != "admin":
                yield from _plain_routes(entry.url_patterns, route)
        elif isinstance(entry, URLPattern) and "<" not in route and "(" not in route:
            yield "/" + route.lstrip("^").rstrip("$"), entry.name


class EveryRouteNeedsSignInTests(TestCase):
    """Article 1 at its widest: a new page is private unless it is listed
    here on purpose. Routes that take arguments need their own ownership
    tests beside the view."""

    PUBLIC_NAMES = {"login"}
    # Invented content, DEBUG only (config/urls.py).
    PUBLIC_PREFIXES = ("/styleguide/",)

    # Catches a view added without login_required.
    def test_signed_out_get_never_returns_a_page(self):
        for path, name in _plain_routes():
            if name in self.PUBLIC_NAMES or path.startswith(self.PUBLIC_PREFIXES):
                continue
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertIn(response.status_code, (301, 302, 401, 403, 404, 405))
                if response.status_code in (301, 302):
                    self.assertIn("/accounts/login/", response["Location"])


class AdminIsSuperuserOnlyTests(TestCase):
    # Catches is_staff alone opening the admin: it shows every record.
    def test_staff_who_are_not_superusers_cannot_open_the_admin(self):
        staff = User.objects.create_user(username="staff-qz", password="x" * 16, is_staff=True)
        self.client.force_login(staff)
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])

    def test_superuser_can_open_the_admin(self):
        self.client.force_login(User.objects.create_superuser(username="admin-qz", password="x" * 16))
        self.assertEqual(self.client.get("/admin/").status_code, 200)


class ErrorPageTests(TestCase):
    # Catches the 404 naming the path, or losing the house style.
    def test_missing_page_uses_our_template_and_does_not_echo_the_path(self):
        response = self.client.get("/no-such-page-qz/")
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "404.html")
        self.assertNotContains(response, "no-such-page-qz", status_code=404)

    # Catches the 500 page needing context: it is rendered with none, and a
    # {% url %} or a user in it turns one error into two.
    def test_the_500_page_renders_with_no_context(self):
        self.assertIn("Something went wrong", render_to_string("500.html"))


class NoStoredUploadsTests(TestCase):
    """Nothing takes a file yet. Delete this class in the change that
    designs the first upload, with the Purser (article 6)."""

    # Catches a /media/ route: it would serve whatever lands on disk to
    # anyone who can guess a filename.
    def test_there_is_no_media_route(self):
        self.client.force_login(User.objects.create_user(username="staff-qz", password="x" * 16))
        self.assertEqual(self.client.get("/media/anything").status_code, 404)

    # Catches a FileField starting to keep files silently.
    def test_no_model_has_a_file_field(self):
        offenders = [
            f"{model._meta.label}.{field.name}"
            for model in apps.get_models()
            for field in model._meta.get_fields()
            if isinstance(field, models.FileField)
        ]
        self.assertEqual(offenders, [])


class DeployHelperTests(SimpleTestCase):
    """settings.py relies on these for ALLOWED_HOSTS, the DEBUG guard and
    the database."""

    # Catches a laptop being treated as deployed, or Azure not being.
    def test_only_app_service_counts_as_deployed(self):
        self.assertFalse(is_deployed({}))
        self.assertTrue(is_deployed({"WEBSITE_HOSTNAME": "a.azurewebsites.net"}))

    # Catches a deployed site booting on an empty SQLite file because a
    # setting was forgotten.
    def test_a_deployed_site_without_postgres_refuses_to_start(self):
        with self.assertRaises(RuntimeError):
            database_config({"WEBSITE_HOSTNAME": "a.azurewebsites.net"}, "db.sqlite3")

    # Catches a deployed connection falling back to plain text.
    def test_a_deployed_site_refuses_a_weak_sslmode(self):
        env = {"WEBSITE_HOSTNAME": "a", "POSTGRES_HOST": "h", "POSTGRES_DB": "d",
               "POSTGRES_USER": "u", "POSTGRES_SSLMODE": "prefer"}
        with self.assertRaises(RuntimeError):
            database_config(env, "db.sqlite3")

    # Catches an unresolved Key Vault reference being used as a secret:
    # its own text is public knowledge.
    def test_unresolved_key_vault_references_are_named_not_shown(self):
        env = {"SECRET_KEY": "@Microsoft.KeyVault(SecretUri=https://x)", "OTHER": "fine"}
        self.assertEqual(unresolved_key_vault_references(env), ["SECRET_KEY"])
