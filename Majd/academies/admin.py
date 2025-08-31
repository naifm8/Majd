from django.contrib import admin
from django.utils.html import format_html
from .models import Academy, Program, Session, SessionSlot, TrainingClass
from django.contrib import admin
from .models import PlanType, SessionSkill, Position, SkillDefinition


from django import forms
from django.urls import path
from django.shortcuts import redirect
from django.contrib import messages
from django.template.response import TemplateResponse

class ProgramInline(admin.TabularInline):
    model = Program
    extra = 1
    fields = ("title", "sport_type", "short_description")

@admin.register(Academy)
class AcademyAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "email", "establishment_year", "owner")
    search_fields = ("name", "city")
    list_filter = ("city", "establishment_year")
    inlines = [ProgramInline]  

    def logo_preview(self, obj):
        if obj.logo:
            return format_html(f'<img src="{obj.logo.url}" width="60" height="60" style="object-fit:cover;border-radius:5px;" />')
        return "No Logo"

    logo_preview.short_description = "Logo"
    

class SessionInline(admin.TabularInline):
    model = Session
    extra = 1
    fields = ("title", "trainer", "level", "start_datetime", "end_datetime")  # ✅ ✅
    
class SessionSkillInline(admin.TabularInline):
    model = SessionSkill
    extra = 1
    autocomplete_fields = ["skill"]

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ("title", "academy", "sport_type")
    list_filter = ("sport_type", "academy")
    search_fields = ("title",)
    # inlines = [SessionInline]

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("title", "program", "trainer", "level", "gender", "capacity", "start_datetime", "end_datetime", "generate_classes_link")
    list_filter = ("level", "gender")
    search_fields = ("title",)
    date_hierarchy = "start_datetime"
    actions = ["generate_training_classes"]
    inlines = [SessionSkillInline]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:session_id>/import-skills/",
                self.admin_site.admin_view(self.import_skills_view),
                name="import_session_skills",
            ),
        ]
        return custom_urls + urls

    def import_skills_view(self, request, session_id):
        session = self.get_object(request, session_id)
        if request.method == "POST":
            form = ImportSkillsForm(request.POST)
            if form.is_valid():
                position = form.cleaned_data["position"]
                skills = SkillDefinition.objects.filter(position=position)
                count = 0
                for s in skills:
                    _, created = SessionSkill.objects.get_or_create(
                        session=session,
                        skill=s,
                        defaults={"target_level": 100}
                    )
                    if created:
                        count += 1
                self.message_user(request, f"✅ تم استيراد {count} مهارة من مركز {position.name}")
                return redirect(f"../../{session_id}/change/")
        else:
            form = ImportSkillsForm()

        context = dict(
            self.admin_site.each_context(request),
            form=form,
            session=session,
            opts=self.model._meta,
        )
        return TemplateResponse(request, "admin/import_skills.html", context)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["import_skills_url"] = f"{object_id}/import-skills/"
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def generate_training_classes(self, request, queryset):
        count = 0
        for session in queryset:
            session.generate_classes()
            count += 1
        self.message_user(request, f"تم توليد الحصص لـ {count} جلسة بنجاح ✅")

    generate_training_classes.short_description = "🔄 توليد الحصص (Training Classes) للجلسات المحددة"

    def generate_classes_link(self, obj):
        return format_html("<span style='color:green;'>⚡️ استخدم الإجراء أعلاه لتوليد الحصص</span>")

    generate_classes_link.short_description = "توليد الحصص"



@admin.register(SessionSlot)
class SessionSlotAdmin(admin.ModelAdmin):
    list_display = ("session", "weekday", "start_time", "end_time")
    list_filter = ("weekday", "session")
    
    
class SkillDefinitionInline(admin.TabularInline):
    model = SkillDefinition
    extra = 1
    
@admin.register(SkillDefinition)
class SkillDefinitionAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("name", "position")
    
@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    inlines = [SkillDefinitionInline]
    
    
class ImportSkillsForm(forms.Form):
    position = forms.ModelChoiceField(queryset=Position.objects.all(), label="اختر المركز")


@admin.register(TrainingClass)
class TrainingClassAdmin(admin.ModelAdmin):
    list_display = ("session", "date", "start_time", "end_time", "topic")
    list_filter = ("session", "date")
    search_fields = ("session__title", "topic")
    date_hierarchy = "date"


@admin.register(PlanType)
class PlanTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)


# @admin.register(SubscriptionPlan)
# class SubscriptionPlanAdmin(admin.ModelAdmin):
#     list_display = ("academy", "name", "price", "duration_days", "is_active")
#     list_filter = ("is_active", "academy")

