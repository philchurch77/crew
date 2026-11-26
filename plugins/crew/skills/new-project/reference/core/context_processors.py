from django.conf import settings


def names(request):
    """The top bar's names, for layout.html."""
    return {"product_name": settings.PRODUCT_NAME, "client_name": settings.CLIENT_NAME}
