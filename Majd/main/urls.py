from django.urls import path
from . import views

app_name = "main"


urlpatterns = [
    path('', views.main_home_view, name='main_home_view'),
    path('contact/', views.contact_view, name='contact_view'),
    path('ourVision/', views.our_vision_view, name='our_vision_view'),
]
