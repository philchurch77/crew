from django.conf import settings


class ContentSecurityPolicyMiddleware:
    """Set the Content-Security-Policy header from ``settings.SECURE_CSP``,
    so chat content cannot be carried off in a URL. Shaped like Django 6.0's
    setting, so upgrading swaps this class for Django's. Never reads the
    body (a stream has none)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Django's DEBUG error pages are inline; let them render.
        if settings.DEBUG and response.status_code >= 400:
            return response
        # Per response, so override_settings works.
        policy = "; ".join(
            f"{directive} {' '.join(sources)}"
            for directive, sources in settings.SECURE_CSP.items()
        )
        response.headers.setdefault("Content-Security-Policy", policy)
        return response
