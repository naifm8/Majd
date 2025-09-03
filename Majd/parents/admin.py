from django.contrib import admin
from .models import Child, Enrollment
# Register your models here.
admin.site.register(Child)

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("child", "program", "session_list", "is_active", "payment_status")

    def session_list(self, obj):
        return ", ".join(s.title for s in obj.sessions.all())
    session_list.short_description = "Sessions"
