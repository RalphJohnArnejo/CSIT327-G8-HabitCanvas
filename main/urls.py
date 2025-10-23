from django.urls import path
from django.contrib.auth import views as auth_views
from .views import landing_view, register_view, login_view, dashboard_view, logout_view

urlpatterns = [
    # Landing page (homepage)
    path("", landing_view, name="landing"),

    # Authentication routes
    path("register/", register_view, name="register"),
    path("login/", login_view, name="login"),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("logout/", logout_view, name="logout"),

    # User dashboard
    path("dashboard/", dashboard_view, name="dashboard"),

    # Built-in Password Reset Views
    path("password_reset/", auth_views.PasswordResetView.as_view(), name="password_reset"),
    path("password_reset/done/", auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),
]
