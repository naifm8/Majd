from django.urls import path
from . import views

app_name = "communication"

urlpatterns = [
    # Trainer
    path("conversations/", views.trainer_conversations_view, name="trainer_conversations_view"),
    path("conversations/<int:conversation_id>/", views.trainer_conversation_detail_view, name="trainer_conversation_detail"),
    
    # Parent
    path("parent/conversations/", views.parent_conversations_view, name="parent_conversations_view"),
    path("parent/conversations/<int:conversation_id>/", views.parent_conversation_detail_view, name="parent_conversation_detail"),
    
    # Both
    path("start/", views.start_conversation_view, name="start_conversation"),

]
