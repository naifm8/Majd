from django.contrib import admin
from django.utils.html import format_html
from .models import Academy, Program, Session, SessionSlot, TrainingClass


@admin.register(Academy)
class AcademyAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "email", "establishment_year", "owner")
    search_fields = ("name", "city")
    list_filter = ("city", "establishment_year")


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ("title", "academy", "sport_type")
    list_filter = ("sport_type", "academy")
    search_fields = ("title",)


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("title", "program", "trainer", "level", "gender", "capacity", "start_date", "end_date", "generate_classes_link")
    list_filter = ("level", "gender", "program__academy")
    search_fields = ("title",)
    date_hierarchy = "start_date"

    # ✅ Action لتوليد الحصص
    actions = ["generate_training_classes"]

    def generate_training_classes(self, request, queryset):
        count = 0
        for session in queryset:
            session.generate_classes()
            count += 1
        self.message_user(request, f"تم توليد الحصص لـ {count} جلسة بنجاح ✅")

    generate_training_classes.short_description = "🔄 توليد الحصص (Training Classes) للجلسات المحددة"

    # ✅ زر مباشر في القائمة
    def generate_classes_link(self, obj):
        return format_html("<span style='color:green;'>⚡️ استخدم الإجراء أعلاه لتوليد الحصص</span>")

    generate_classes_link.short_description = "توليد الحصص"


@admin.register(SessionSlot)
class SessionSlotAdmin(admin.ModelAdmin):
    list_display = ("session", "weekday", "start_time", "end_time")
    list_filter = ("weekday", "session")


@admin.register(TrainingClass)
class TrainingClassAdmin(admin.ModelAdmin):
    list_display = ("session", "date", "start_time", "end_time", "topic")
    list_filter = ("session", "date")
    search_fields = ("session__title", "topic")
    date_hierarchy = "date"
