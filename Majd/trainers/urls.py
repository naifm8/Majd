from django.urls import path
from . import views

app_name = "trainers"

urlpatterns = [
    path("dashboard/overview/", views.overview_view, name="overview_view"),
    path("dashboard/students/", views.students_view, name="students_view"),
    path("dashboard/sessions/", views.training_sessions_view, name="training_sessions_view"),

    path("dashboard/attendance/", views.attendance_view, name="attendance_view"),
    path("dashboard/attendance/take/<int:class_id>/", views.take_attendance_view, name="take_attendance"),

    path("dashboard/evaluations/", views.evaluations_view, name="evaluations_view"),
    path("dashboard/evaluations/class/<int:class_id>/", views.take_evaluations_view, name="take_evaluations"),
    path("player/<int:player_id>/edit-position/", views.edit_player_position, name="edit_player_position"),


]
