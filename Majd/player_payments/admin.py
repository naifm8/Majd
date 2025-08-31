from django.contrib import admin
from .models import PlayerSubscription, PlayerEnrollment, PaymentTransaction


@admin.register(PlayerSubscription)
class PlayerSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['title', 'academy', 'program', 'price', 'billing_type', 'is_active', 'created_at']
    list_filter = ['billing_type', 'is_active', 'academy', 'program__sport_type']
    search_fields = ['title', 'academy__name', 'program__title']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'academy', 'program', 'description', 'is_active')
        }),
        ('Pricing', {
            'fields': ('price', 'billing_type')
        }),
        ('Features', {
            'fields': ('program_features', 'subscription_features'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(PlayerEnrollment)
class PlayerEnrollmentAdmin(admin.ModelAdmin):
    list_display = ['child', 'subscription', 'status', 'start_date', 'end_date', 'amount_paid', 'payment_date']
    list_filter = ['status', 'payment_method', 'auto_renewal', 'start_date', 'subscription__academy']
    search_fields = ['child__first_name', 'child__last_name', 'subscription__title', 'parent__username']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Enrollment Details', {
            'fields': ('subscription', 'child', 'parent', 'status')
        }),
        ('Period', {
            'fields': ('start_date', 'end_date', 'auto_renewal')
        }),
        ('Payment Information', {
            'fields': ('amount_paid', 'payment_method', 'transaction_id', 'payment_date')
        }),
        ('Additional Info', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('child', 'subscription', 'parent')


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ['enrollment', 'transaction_type', 'status', 'amount', 'currency', 'created_at', 'processed_at']
    list_filter = ['transaction_type', 'status', 'currency', 'created_at']
    search_fields = ['enrollment__child__first_name', 'enrollment__child__last_name', 'gateway_transaction_id']
    readonly_fields = ['created_at', 'processed_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('enrollment', 'transaction_type', 'status', 'amount', 'currency')
        }),
        ('Gateway Information', {
            'fields': ('gateway_transaction_id', 'gateway_response'),
            'classes': ('collapse',)
        }),
        ('Additional Info', {
            'fields': ('notes', 'failure_reason'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'processed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('enrollment__child', 'enrollment__subscription')


# Additional admin configurations
admin.site.site_header = "Majd Player Payments Administration"
admin.site.site_title = "Majd Player Payments Admin"
admin.site.index_title = "Welcome to Majd Player Payments Administration"
