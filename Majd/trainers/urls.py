from django.urls import path
from . import views

app_name = "trainers"

urlpatterns = [
    path("dashboard/overview", views.overview_view, name="overview_view"),
]
