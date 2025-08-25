from django.contrib import admin
from .models import (
    PlayerProfile, PlayerSkill, TrainingProgram, 
    TrainingSession, PlayerSession, Achievement, Evaluation
)

# ✅ PlayerProfile مع عرض التقدّم والدرجة
@admin.register(PlayerProfile)
class PlayerProfileAdmin(admin.ModelAdmin):
    list_display = ("child", "academy_name", "attendance_rate", "avg_progress", "current_grade")
    readonly_fields = ("avg_progress", "current_grade")  # ما تنعدل يدوي

# ✅ Evaluation
@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ("player", "score", "coach", "session", "created_at")
    list_filter = ("player", "coach", "created_at")
    search_fields = ("player__child__first_name", "player__child__last_name", "feedback")

# باقي الموديلات تسجيل عادي
admin.site.register(PlayerSkill)
admin.site.register(TrainingProgram)
admin.site.register(TrainingSession)
admin.site.register(PlayerSession)
admin.site.register(Achievement)
