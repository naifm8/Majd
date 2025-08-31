from django.contrib import admin
from django.contrib import admin
from .models import ClassPlan, TrainingNote
# Register your models here.



@admin.register(ClassPlan)
class ClassPlanAdmin(admin.ModelAdmin):
    list_display = ("training_class", "trainer", "status", "updated_at")
    search_fields = ("training_class__session__title", "trainer__user__username")
    list_filter = ("status",)

@admin.register(TrainingNote)
class TrainingNoteAdmin(admin.ModelAdmin):
    list_display = ("training_class", "trainer", "player", "note_type", "created_at")
    search_fields = ("training_class__session__title", "trainer__user__username", "player__child__first_name", "player__child__last_name")
    list_filter = ("note_type",)
