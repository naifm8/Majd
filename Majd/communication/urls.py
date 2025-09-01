from django.urls import path
from . import views

app_name = "communication"

urlpatterns = [
    path("conversations/", views.conversations_list_view, name="conversations_list"),
    path("conversations/<int:conversation_id>/", views.conversation_detail_view, name="conversation_detail"),
]
