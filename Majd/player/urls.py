from django.urls import path
from . import views

app_name = "player"

urlpatterns = [
    path("dashboard/<int:child_id>/", views.player_dashboard_view, name="player_dashboard_view"),
]
