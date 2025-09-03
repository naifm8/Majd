from django.urls import path
from . import views

app_name = "academies"

urlpatterns = [
    # Academy
    path("", views.academy_list_view, name="list"),
    path("setup/", views.academy_setup_view, name="setup"),
    path("dashboard/", views.AcademyDashboardView, name="dashboard"),
    path("dashboard/subscriptions/", views.subscription_dashboard, name="subscription_dashboard"),
    path("dashboard/subscriptions/add/", views.add_subscription_plan, name="add_subscription_plan"),
    path("dashboard/subscriptions/<int:plan_id>/edit/", views.edit_subscription_plan, name="edit_subscription_plan"),
    path("dashboard/subscriptions/<int:plan_id>/delete/", views.delete_subscription_plan, name="delete_subscription_plan"),
    # Subscription Enrollment
    path("<slug:academy_slug>/subscription/<int:plan_id>/enroll/", views.subscription_enroll_redirect, name="subscription_enroll_redirect"),

    # Trainer 
    path("trainers/", views.trainer_dashboard, name="trainer_dashboard"),
    path("trainers/add/", views.add_trainer, name="add_trainer"),

    # Academy detail
    path("<slug:slug>/", views.AcademyDetailView, name="detail"),
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
    path("<slug:academy_slug>/program/<int:program_id>/sessions/", views.enrollment_sessions_view, name="enrollment_sessions"),
    path("<slug:academy_slug>/program/<int:program_id>/enrollment-details/", views.enrollment_details_view, name="enrollment_details"),
    path("<slug:academy_slug>/<int:program_id>/sessions/",views.program_sessions,name="program_sessions"),
    

    # Players
    path("dashboard/players/", views.players_dashboard, name="players_dashboard"),

]

