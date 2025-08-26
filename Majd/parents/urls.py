from django.urls import path
from . import views

app_name = "parents"


urlpatterns = [
    path('dashboard/overview/', views.dashboard_view, name='dashboard_view'),
    path('dashboard/children/', views.my_children_view, name='my_children_view'),
]
