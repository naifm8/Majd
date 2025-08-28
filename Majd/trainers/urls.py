from django.urls import path
from . import views

app_name = "trainers"

urlpatterns = [
    path("dashboard/", views.teain_dashboard_view, name="teain_dashboard_view"),
]
