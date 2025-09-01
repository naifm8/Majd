from django.urls import path
from . import views

from . import views

app_name = "academies"

urlpatterns = [
    path("", views.academy_list_view, name="list"),
    path("setup/", views.academy_setup_view, name="setup"),
    path("dashboard/", views.AcademyDashboardView, name="dashboard"),

    # Trainer 
    path("trainers/", views.trainer_dashboard, name="trainer_dashboard"),
    path("trainers/add/", views.add_trainer, name="add_trainer"),

    # Academy
    path("<slug:slug>/", views.AcademyDetailView, name="detail"),
    path("<slug:slug>/join/", views.join_academy_view, name="join_academy_view"),
    path("<slug:academy_slug>/program/<int:program_id>/join/", views.join_program_view, name="join_program_view"),


    # Programs
    path("dashboard/programs/", views.program_dashboard, name="programs"),
    path("dashboard/programs/create/", views.program_create, name="program_create"),
    path("dashboard/programs/<int:pk>/edit/", views.program_edit, name="program_edit"),
    path("dashboard/programs/<int:pk>/delete/", views.program_delete, name="program_delete"),


    # Sessions
    path("dashboard/programs/<int:program_id>/sessions/create/", views.session_create, name="session_create"),
    path("dashboard/sessions/<int:pk>/edit/", views.session_edit, name="session_edit"),
    path("dashboard/sessions/<int:pk>/delete/", views.session_delete, name="session_delete"),
    path("<slug:academy_slug>/<int:program_id>/sessions/", 
         views.program_sessions, 
         name="program_sessions"),


]

