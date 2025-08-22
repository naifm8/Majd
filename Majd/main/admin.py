# contact/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import ContactMessage
from main import models

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    # Columns in the changelist
    list_display = (
        "full_name", "email", "inquiry_badge", "subject",
        "organization", "created_at",
    )
    # Clickable columns (links to the change page)
    list_display_links = ("full_name", "subject")
    # Right-side filters
    list_filter = ("inquiry_type", "created_at")
    # Search bar (supports icontains on text fields)
    search_fields = ("full_name", "email", "subject", "message", "organization", "phone")
    # Ordering (desc by date)
    ordering = ("-created_at",)
    # Pagination
    list_per_page = 25
    # Date navigator above the list
    date_hierarchy = "created_at"


    # Detail page layout
    fieldsets = (
        ("Contact", {
            "fields": ("full_name", "email", "phone", "organization")
        }),
        ("Inquiry", {
            "fields": ("inquiry_type", "subject", "message")
        }),
        ("Meta", {
            "fields": ("created_at",),
        }),
    )
    readonly_fields = ("created_at",)

    # Custom colored badge column
    def inquiry_badge(self, obj):
        colors = {
            "general":  "#0d6efd",  # blue
            "partner":  "#20c997",  # teal
            "sponsor":  "#fd7e14",  # orange
            "academy":  "#6f42c1",  # purple
            "tech":     "#198754",  # green
            "media":    "#d63384",  # pink
        }
        label = dict(ContactMessage.INQUIRY_CHOICES).get(obj.inquiry_type, obj.inquiry_type)
        color = colors.get(obj.inquiry_type, "#6c757d")
        return format_html(
            '<span style="padding:.2rem .5rem;border-radius:.5rem;background:{}20;color:{};border:1px solid {}40;">{}</span>',
            color, color, color, label
        )
    inquiry_badge.short_description = "Inquiry Type"
    inquiry_badge.admin_order_field = "inquiry_type"
    
class CorporateEmailFilter(admin.SimpleListFilter):
    title = "Email type"
    parameter_name = "email_kind"

    def lookups(self, request, model_admin):
        return (("corp", "Corporate domain"), ("free", "Free email provider"))

    def queryset(self, request, queryset):
        free = ("gmail.com","yahoo.com","outlook.com","hotmail.com","icloud.com")
        if self.value() == "corp":
            return queryset.exclude(email__iendswith=free)
        if self.value() == "free":
            q = None
            for d in free:
                q = (q | models.Q(email__iendswith=d)) if q else models.Q(email__iendswith=d)
            return queryset.filter(q)
        return queryset
