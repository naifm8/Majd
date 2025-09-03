from django.urls import path
from . import views

app_name = "parents"

urlpatterns = [
    path("", views.parent_dashboard_view, name="dashboard"),
    path("children/", views.my_children_view, name="children"),
    path("add-child/", views.add_child_view, name="add_child"),
    path("edit-child/<int:child_id>/", views.edit_child_view, name="edit_child"),
    path("delete-child/<int:child_id>/", views.delete_child_view, name="delete_child"),
    path("schedule/", views.schedule_view, name="schedule"),
    path("payments/", views.payments_view, name="payments"),
    path("reports/", views.reports_view, name="reports"),
    path("subscriptions/", views.subscriptions_view, name="subscriptions"),
    path("settings/", views.settings_view, name="settings"),
    path("unenroll/<int:session_id>/<int:child_id>/", views.unenroll_view, name="unenroll"),
    path("edit-profile/", views.edit_profile_view, name="edit_profile"),
    # New enrollment URLs
    path("enroll/", views.enroll_child, name="enroll_child"),
    path("enrollment/<int:enrollment_id>/pause/", views.pause_enrollment, name="pause_enrollment"),
    path("enrollment/<int:enrollment_id>/resume/", views.resume_enrollment, name="resume_enrollment"),
    
    # Payment URLs
    path("process-payment/", views.process_payment, name="process_payment"),
]
