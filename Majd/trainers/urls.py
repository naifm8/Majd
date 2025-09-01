from django.urls import path
from . import views

app_name = "trainers"

urlpatterns = [
    path("dashboard/overview/", views.overview_view, name="overview_view"),
    path("dashboard/students/", views.students_view, name="students_view"),
    path("dashboard/sessions/", views.training_sessions_view, name="training_sessions_view"),
    # path("dashboard/classes/", views.all_classes_view, name="all_classes"),
    # path("dashboard/take/", views.take_attendance_view, name="take_attendance"),

]
