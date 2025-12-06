from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    landing_view, register_view, login_view, dashboard_view, logout_view,
    add_task, edit_task, delete_task, toggle_complete, toggle_favorite,
    timer_view,
    # Subtask views
    add_subtask, toggle_subtask, delete_subtask, get_subtasks
)

urlpatterns = [
    # Landing page
    path("", landing_view, name="landing"),

    # Authentication
    path("register/", register_view, name="register"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),

    # Dashboard / Tasks
    path("dashboard/", dashboard_view, name="dashboard"),
    path("tasks/", dashboard_view, name="tasks"),  # tasks list now handled by dashboard_view
    path("tasks/add/", add_task, name="add_task"),
    path("tasks/edit/<int:task_id>/", edit_task, name="edit_task"),
    path("tasks/delete/<int:task_id>/", delete_task, name="delete_task"),
    path("tasks/toggle_complete/<int:task_id>/", toggle_complete, name="toggle_complete"),
    path("tasks/toggle_favorite/<int:task_id>/", toggle_favorite, name="toggle_favorite"),

    # Timer Page
    path("timer/", timer_view, name="timer"),

    # Subtasks
    path("tasks/<int:task_id>/subtasks/", get_subtasks, name="get_subtasks"),
    path("tasks/<int:task_id>/subtasks/add/", add_subtask, name="add_subtask"),
    path("subtasks/<int:subtask_id>/toggle/", toggle_subtask, name="toggle_subtask"),
    path("subtasks/<int:subtask_id>/delete/", delete_subtask, name="delete_subtask"),

    # Password reset
    path("password_reset/", auth_views.PasswordResetView.as_view(), name="password_reset"),
    path("password_reset/done/", auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),
]
