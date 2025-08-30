from django.urls import path
from .views import academy_list_view, AcademyDetailView, academy_setup_view, AcademyDashboardView
from . import views

app_name = "academies"

urlpatterns = [
    path("", academy_list_view, name="list"),
    path("setup/", academy_setup_view, name="setup"),
    path("dashboard/", AcademyDashboardView.as_view(), name="dashboard"),
    path("<slug:slug>/", AcademyDetailView.as_view(), name="detail"),
    path("<slug:slug>/join/", views.join_academy_view, name="join_academy_view"),
]
