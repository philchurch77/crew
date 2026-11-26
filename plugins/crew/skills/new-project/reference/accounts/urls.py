"""Authentication routes, mounted one by one. No password reset until the
project has an email backend; password change, so an admin-set password
need not last. Accounts are made in the admin."""
from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(
        template_name="accounts/login.html",
        redirect_authenticated_user=True,
    ), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("password/", auth_views.PasswordChangeView.as_view(
        template_name="accounts/password_change.html",
        success_url=reverse_lazy("password_change_done"),
    ), name="password_change"),
    path("password/done/", auth_views.PasswordChangeDoneView.as_view(
        template_name="accounts/password_change_done.html",
    ), name="password_change_done"),
]
