from django.urls import path
from . import views

app_name = "parents"


urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard_view'),
]
