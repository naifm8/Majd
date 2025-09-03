from django.db import models
from django.contrib.auth.models import User
from academies.models import Academy, Program
from parents.models import Child


class PlayerSubscription(models.Model):
    BILLING_CHOICES = [
        ("3m", "3 Months"),
        ("6m", "6 Months"),
        ("12m", "12 Months"),
    ]

    title = models.CharField(max_length=120)  
    academy = models.ForeignKey(Academy, on_delete=models.CASCADE, related_name="player_subscriptions")
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="player_subscriptions", blank=True, null=True)

    price = models.DecimalField(max_digits=8, decimal_places=2)
    billing_type = models.CharField(max_length=20, choices=BILLING_CHOICES)

    description = models.TextField(blank=True)

    # Program-specific features (can vary by plan)
    program_features = models.JSONField(default=list, blank=True)

    # Core subscription benefits (default across all plans)
    subscription_features = models.JSONField(
        default=list,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} ({self.get_billing_type_display()})"

    def price_display(self):
        return f"${self.price} / {self.get_billing_type_display()}"

    def get_subscription_features(self):
        """Get subscription features with defaults if none are set"""
        if self.subscription_features:
            return self.subscription_features
        return [
            "To be trained by top and skilled trainers",
            "Generating reports of each class by the trainer", 
            "Player dashboard to track progress",
            "Real time parent connection via dashboard",
            "Many sport types to choose from",
        ]

    def save(self, *args, **kwargs):
        """Set default subscription features if none provided"""
        if not self.subscription_features:
            self.subscription_features = [
                "To be trained by top and skilled trainers",
                "Generating reports of each class by the trainer",
                "Player dashboard to track progress", 
                "Real time parent connection via dashboard",
                "Many sport types to choose from",
            ]
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['academy', 'price']


class PlayerEnrollment(models.Model):
    """Track individual player enrollments in subscription plans"""
    
    STATUS_CHOICES = [
        ("pending", "Pending Payment"),
        ("active", "Active"),
        ("expired", "Expired"),
        ("cancelled", "Cancelled"),
    ]

    PAYMENT_METHOD_CHOICES = [
        ("card", "Credit/Debit Card"),
        ("transfer", "Bank Transfer"),
        ("cash", "Cash Payment"),
    ]

    # Subscription and student info
    subscription = models.ForeignKey(PlayerSubscription, on_delete=models.CASCADE, related_name="enrollments")
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name="payment_enrollments")
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name="child_enrollments")

    # Payment and status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default="card")
    transaction_id = models.CharField(max_length=100, blank=True, null=True)

    # Enrollment period
    start_date = models.DateField()
    end_date = models.DateField()
    auto_renewal = models.BooleanField(default=False)

    # Financial tracking
    amount_paid = models.DecimalField(max_digits=8, decimal_places=2)
    payment_date = models.DateTimeField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    def _str_(self):
        return f"{self.child.first_name} - {self.subscription.title} ({self.status})"

    @property
    def is_active(self):
        from django.utils import timezone
        return self.status == "active" and self.end_date >= timezone.now().date()

    @property
    def days_remaining(self):
        from django.utils import timezone
        if self.status == "active":
            delta = self.end_date - timezone.now().date()
            return max(0, delta.days)
        return 0

    class Meta:
        ordering = ['-created_at']
        unique_together = ['subscription', 'child', 'start_date']


class PaymentTransaction(models.Model):
    """Track payment transactions for enrollments"""
    
    TRANSACTION_TYPE_CHOICES = [
        ("initial", "Initial Payment"),
        ("renewal", "Renewal Payment"),
        ("refund", "Refund"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]

    enrollment = models.ForeignKey(PlayerEnrollment, on_delete=models.CASCADE, related_name="transactions")
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES, default="initial")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    amount = models.DecimalField(max_digits=8, decimal_places=2)
    currency = models.CharField(max_length=3, default="SAR")
    
    # Payment gateway info
    gateway_transaction_id = models.CharField(max_length=200, blank=True, null=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Additional info
    notes = models.TextField(blank=True)
    failure_reason = models.TextField(blank=True)

    def __str__(self):
        return f"{self.enrollment.child.first_name} - {self.amount} {self.currency} ({self.status})"

    class Meta:
        ordering = ['-created_at']
