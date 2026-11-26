from django.conf import settings
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import include, path
from django.views.generic import TemplateView

# Superusers only, enforced here: the admin shows every record, and a staff
# user with change_user could grant itself access.
admin.site.has_permission = lambda request: (
    request.user.is_active and request.user.is_superuser
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", login_required(TemplateView.as_view(template_name="home.html")), name="home"),
    path("accounts/", include("accounts.urls")),
]

# The house style on show, with invented content. Never on a deployed site.
if settings.DEBUG:
    urlpatterns += [
        path("styleguide/", TemplateView.as_view(template_name="styleguide.html")),
        path("styleguide/chat/", TemplateView.as_view(template_name="styleguide_chat.html")),
    ]

# WhiteNoise serves static files. No media route: nothing is written to disk.
