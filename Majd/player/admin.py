from django.contrib import admin
from .models import (
    PlayerProfile,
    PlayerSkill,
    PlayerSession,
    Achievement,
    Evaluation,
    PlayerClassAttendance,
)



@admin.register(PlayerProfile)
class PlayerProfileAdmin(admin.ModelAdmin):
    list_display = ("child", "academy", "attendance_rate", "avg_progress", "current_grade")
    readonly_fields = ("attendance_rate", "avg_progress", "current_grade")  # ✅ أضف هنا
    list_filter = ("academy",)





@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ("player", "score", "coach", "training_class", "created_at")
    list_filter = ("training_class__session", "coach", "created_at")
    search_fields = ("player__child__first_name", "player__child__last_name", "feedback")



@admin.register(PlayerClassAttendance)
class PlayerClassAttendanceAdmin(admin.ModelAdmin):
    list_display = ("player", "training_class", "status")
    list_filter = ("status", "training_class__session")
    search_fields = ("player__child__first_name", "player__child__last_name")



admin.site.register(PlayerSkill)
admin.site.register(PlayerSession)
admin.site.register(Achievement)
