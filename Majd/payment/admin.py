from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import PlanType, SubscriptionPlan, Subscription


@admin.register(PlanType)
class PlanTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ("academy", "plan_type", "price", "duration_days", "is_active", "created_at")
    list_filter = ("is_active", "plan_type", "academy")
    search_fields = ("academy__name", "plan_type__name")


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'academy_name', 'plan_type', 'status', 'price', 'payment_method', 
        'contact_email', 'created_at', 'payment_date'
    ]
    list_filter = [
        'status', 'payment_method', 'created_at', 'payment_date', 'plan_type'
    ]
    search_fields = [
        'academy_name', 'plan_type__name', 'contact_email', 'transaction_id'
    ]
    readonly_fields = ['created_at', 'updated_at', 'notes']
    
    fieldsets = (
        ('Academy Information', {
            'fields': ('academy_name', 'plan_type', 'contact_email', 'contact_phone', 'billing_address')
        }),
        ('Subscription Details', {
            'fields': ('price', 'duration_days', 'start_date', 'end_date')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'transaction_id', 'status', 'payment_date')
        }),
        ('Additional Information', {
            'fields': ('notes', 'error_message', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['send_invoice_email', 'mark_as_successful', 'mark_as_failed']
    
    def send_invoice_email(self, request, queryset):
        """Admin action to send invoice emails"""
        sent_count = 0
        for subscription in queryset:
            try:
                subscription.send_invoice()
                sent_count += 1
            except Exception as e:
                self.message_user(
                    request, 
                    f"Failed to send invoice for {subscription}: {str(e)}", 
                    level='ERROR'
                )
        
        if sent_count > 0:
            self.message_user(
                request, 
                f"Successfully sent {sent_count} invoice email(s)"
            )
    send_invoice_email.short_description = "Send invoice emails"
    
    def mark_as_successful(self, request, queryset):
        """Admin action to mark subscriptions as successful"""
        updated = queryset.update(
            status=Subscription.Status.SUCCESSFUL,
            payment_date=timezone.now()
        )
        self.message_user(request, f"Marked {updated} subscription(s) as successful")
    mark_as_successful.short_description = "Mark as successful"
    
    def mark_as_failed(self, request, queryset):
        """Admin action to mark subscriptions as failed"""
        updated = queryset.update(status=Subscription.Status.FAILED)
        self.message_user(request, f"Marked {updated} subscription(s) as failed")
    mark_as_failed.short_description = "Mark as failed"
