from django.contrib import admin
from .models import (
    PlayerProfile,
    PlayerSkill,
    PlayerSession,
    Achievement,
    Evaluation,
    PlayerClassAttendance,
)


# ✅ PlayerProfile مع عرض التقدّم والدرجة
@admin.register(PlayerProfile)
class PlayerProfileAdmin(admin.ModelAdmin):
    list_display = ("child", "trainer", "academy", "attendance_rate", "avg_progress", "current_grade")
    readonly_fields = ("avg_progress", "current_grade")  # ما تنعدل يدوي
    list_filter = ("academy", "trainer")


# ✅ Evaluation (مربوط بالـ TrainingClass)
@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ("player", "score", "coach", "training_class", "created_at")
    list_filter = ("training_class__session", "coach", "created_at")
    search_fields = ("player__child__first_name", "player__child__last_name", "feedback")


# ✅ PlayerClassAttendance (الجديد)
@admin.register(PlayerClassAttendance)
class PlayerClassAttendanceAdmin(admin.ModelAdmin):
    list_display = ("player", "training_class", "status")
    list_filter = ("status", "training_class__session")
    search_fields = ("player__child__first_name", "player__child__last_name")


# باقي الموديلات
admin.site.register(PlayerSkill)
admin.site.register(PlayerSession)
admin.site.register(Achievement)
