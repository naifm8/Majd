from django.urls import path
from . import views

app_name = "accounts"


urlpatterns = [
    path('register/', views.register_view, name='register_view'),
    path('login/', views.login_view, name='login_view'),
    path('selection/', views.selection_view, name='selection_view'),
    path('logout/', views.log_out, name='log_out')

]

