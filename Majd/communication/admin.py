from django.contrib import admin
from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "trainer", "parent", "created_at")
    list_filter = ("trainer", "parent")
    search_fields = ("trainer__user__username", "parent__user__username")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "sender", "body", "sent_at", "is_read")
    list_filter = ("conversation", "sender", "is_read")
    search_fields = ("body", "sender__username")
