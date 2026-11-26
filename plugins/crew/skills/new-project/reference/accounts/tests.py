"""Sign-in, as a browser does it: real POSTs with CSRF, never client.login()."""
from axes.models import AccessAttempt
from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from django.urls import NoReverseMatch, reverse

from accounts.throttle import client_ip, forwarded_address

PASSWORD = "correct-horse-battery-staple"
WRONG_PASSWORD = "wrong-password-guess-7731"
ADDRESS_X = "203.0.113.10"
ADDRESS_Y = "198.51.100.20"


def sign_in(client, username, password, url=None, **extra):
    return client.post(url or reverse("login"), {"username": username, "password": password}, **extra)


class SignInJourneyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="staff", password=PASSWORD)
        self.client = Client(enforce_csrf_checks=True)

    # Catches any break between the sign-in form and the first page.
    def test_someone_can_sign_in_with_csrf_and_reach_home(self):
        self.assertEqual(self.client.get(reverse("login")).status_code, 200)
        response = self.client.post(reverse("login"), {
            "username": "staff", "password": PASSWORD,
            "csrfmiddlewaretoken": self.client.cookies["csrftoken"].value,
        })
        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)
        home = self.client.get(reverse("home"))
        self.assertEqual(home.status_code, 200)
        self.assertContains(home, f'action="{reverse("logout")}"')

    # Catches the sign-in redirect losing where the person was going.
    def test_signed_out_page_redirects_to_sign_in_with_next(self):
        response = self.client.get(reverse("password_change"))
        self.assertRedirects(
            response, f"{reverse('login')}?next={reverse('password_change')}",
            fetch_redirect_response=False,
        )

    # Catches sign-out not ending the session (a shared computer).
    def test_signing_out_ends_the_session(self):
        self.client.get(reverse("login"))
        self.client.post(reverse("login"), {
            "username": "staff", "password": PASSWORD,
            "csrfmiddlewaretoken": self.client.cookies["csrftoken"].value,
        })
        self.assertIn("_auth_user_id", self.client.session)
        # The token rotates on sign-in: read the cookie afresh.
        response = self.client.post(
            reverse("logout"), {"csrfmiddlewaretoken": self.client.cookies["csrftoken"].value}
        )
        self.assertEqual(response["Location"], reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)


class PasswordTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="staff", password=PASSWORD)
        self.client.force_login(self.user)

    # Catches the change form saving nothing, or not keeping the session.
    def test_a_new_password_works_at_the_next_sign_in(self):
        new = "a-different-long-passphrase-88"
        response = self.client.post(reverse("password_change"), {
            "old_password": PASSWORD, "new_password1": new, "new_password2": new,
        })
        self.assertRedirects(response, reverse("password_change_done"))
        self.assertEqual(sign_in(Client(), "staff", new).status_code, 302)

    # Catches the validators being dropped from settings.
    def test_a_short_password_is_refused_and_the_old_one_kept(self):
        response = self.client.post(reverse("password_change"), {
            "old_password": PASSWORD, "new_password1": "short1", "new_password2": "short1",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(sign_in(Client(), "staff", PASSWORD).status_code, 302)

    # Catches password reset being mounted with no email backend behind it.
    def test_password_reset_is_not_mounted(self):
        with self.assertRaises(NoReverseMatch):
            reverse("password_reset")


class LoginThrottleTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="leader-qz", password=PASSWORD)

    def fail(self, times, **extra):
        for _ in range(times):
            sign_in(self.client, extra.pop("username", "leader-qz"), WRONG_PASSWORD, **extra)

    # Catches the throttle being absent: unlimited guesses at a password.
    def test_fifth_wrong_password_from_one_address_locks_that_username(self):
        self.fail(5, REMOTE_ADDR=ADDRESS_X)
        response = sign_in(self.client, "leader-qz", PASSWORD, REMOTE_ADDR=ADDRESS_X)
        self.assertEqual(response.status_code, 429)
        self.assertTemplateUsed(response, "accounts/locked_out.html")
        self.assertNotIn("_auth_user_id", self.client.session)

    # Catches the admin sign-in being a side door round the throttle.
    def test_admin_sign_in_is_throttled_too(self):
        User.objects.create_superuser(username="admin-qz", password=PASSWORD)
        url = reverse("admin:login")
        for _ in range(5):
            sign_in(self.client, "admin-qz", WRONG_PASSWORD, url=url, REMOTE_ADDR=ADDRESS_X)
        response = sign_in(self.client, "admin-qz", PASSWORD, url=url, REMOTE_ADDR=ADDRESS_X)
        self.assertEqual(response.status_code, 429)

    # Catches lockout keyed on username alone: anyone could lock a named
    # person out by typing their username five times.
    def test_locked_username_can_still_sign_in_from_another_address(self):
        self.fail(5, REMOTE_ADDR=ADDRESS_X)
        response = sign_in(self.client, "leader-qz", PASSWORD, REMOTE_ADDR=ADDRESS_Y)
        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)

    # Catches the lockout page confirming which account was targeted, and
    # going out without the policy (axes answers before any view runs).
    def test_lockout_page_does_not_echo_the_username_and_carries_the_csp(self):
        self.fail(5, REMOTE_ADDR=ADDRESS_X)
        response = sign_in(self.client, "leader-qz", PASSWORD, REMOTE_ADDR=ADDRESS_X)
        self.assertNotContains(response, "leader-qz", status_code=429)
        self.assertIn("Content-Security-Policy", response.headers)

    # Catches the attempt log keeping what was typed: often a real password
    # one character off.
    def test_a_failed_attempt_never_stores_the_password(self):
        self.fail(1, REMOTE_ADDR=ADDRESS_X)
        attempt = AccessAttempt.objects.get(username="leader-qz")
        self.assertNotIn(WRONG_PASSWORD, attempt.post_data)


class ClientAddressTests(TestCase):
    def request(self, **meta):
        return type("Request", (), {"META": meta})()

    # Catches the throttle keying on a header anyone can write.
    @override_settings(TRUST_X_FORWARDED_FOR=False)
    def test_untrusted_forwarded_header_is_ignored(self):
        request = self.request(HTTP_X_FORWARDED_FOR="1.2.3.4", REMOTE_ADDR=ADDRESS_X)
        self.assertEqual(client_ip(request), ADDRESS_X)

    # Catches trusting the leftmost entry, which the client writes.
    @override_settings(TRUST_X_FORWARDED_FOR=True)
    def test_trusted_proxy_uses_the_rightmost_entry(self):
        request = self.request(HTTP_X_FORWARDED_FOR=f"1.2.3.4, {ADDRESS_Y}:443", REMOTE_ADDR=ADDRESS_X)
        self.assertEqual(client_ip(request), ADDRESS_Y)

    # Catches raw text reaching axes, which stores an inet: a 500 at sign-in.
    def test_anything_that_is_not_an_address_gives_none(self):
        for junk in ("", "unknown", "1.2.3", "fe80::1%eth0", "<script>"):
            with self.subTest(junk=junk):
                self.assertIsNone(forwarded_address(junk))


class NamesOnTheSignInPageTests(TestCase):
    # Catches the top bar's names using a variable Django's own sign-in
    # view also sets (site_name): the page then shows the server's address.
    @override_settings(PRODUCT_NAME="Beacon-qz", CLIENT_NAME="Northfield-qz")
    def test_the_sign_in_page_shows_the_products_and_the_clients_names(self):
        response = self.client.get(reverse("login"))
        self.assertContains(response, "Beacon-qz")
        self.assertContains(response, "Northfield-qz")
        self.assertNotContains(response, "testserver")
