from django.urls import path
from . import views

app_name = "main"


urlpatterns = [
    path('', views.main_home_view, name='main_home_view'),
]
