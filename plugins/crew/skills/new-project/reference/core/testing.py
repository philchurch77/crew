"""Django's test runner with a fast password hasher. Tests only;
override_settings so Django's hasher cache is cleared.
"""

from django.test import override_settings
from django.test.runner import DiscoverRunner


class FastHasherRunner(DiscoverRunner):
    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        self._hashers = override_settings(
            PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"]
        )
        self._hashers.enable()

    def teardown_test_environment(self, **kwargs):
        self._hashers.disable()
        super().teardown_test_environment(**kwargs)
