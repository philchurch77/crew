from django.conf import settings


def assistant(request):
    """The assistant's name, for chat.html and its partials."""
    return {"assistant_name": settings.ASSISTANT_NAME}
