from django.db import models
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone


class PlanType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    monthly_price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    yearly_price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    features = models.JSONField(default=list, blank=True)
    icon_class = models.CharField(max_length=50, default="bi-app")
    is_featured = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name


class SubscriptionPlan(models.Model):
    BILLING_TYPE_CHOICES = [
        ('3m', '3-Month'),
        ('6m', '6-Month'),
        ('12m', '12-Month'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    
    title = models.CharField(max_length=200, default="Subscription Plan")
    academy = models.ForeignKey(
        "academies.Academy",
        on_delete=models.CASCADE,
        related_name="plans",
    )
    plan_type = models.ForeignKey(
        PlanType,
        on_delete=models.CASCADE,
        related_name="subscription_plans",
        null=True,
        blank=True,
    )

    price = models.DecimalField(max_digits=8, decimal_places=2)
    billing_type = models.CharField(
        max_length=10,
        choices=BILLING_TYPE_CHOICES,
        default='monthly'
    )
    description = models.TextField(blank=True, null=True)
    program_features = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.academy.name} - {self.title} (${self.price})"

    class Meta:
        unique_together = ("academy", "title")


class Subscription(models.Model):
    """Track individual subscription attempts and their status"""
    
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESSFUL = "successful", "Successful"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"
    
    class PaymentMethod(models.TextChoices):
        CARD = "card", "Credit/Debit Card"
        TRANSFER = "transfer", "Bank Transfer"
    
    # Academy and plan information
    academy_name = models.CharField(max_length=200)  # Academy name from checkout form
    plan_type = models.ForeignKey(
        PlanType,
        on_delete=models.CASCADE,
        related_name="subscriptions"
    )
    
    # Subscription details
    price = models.DecimalField(max_digits=8, decimal_places=2)
    duration_days = models.PositiveIntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Payment information
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CARD
    )
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    # Contact information from checkout
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20, blank=True)
    billing_address = models.TextField()
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    
    # Notes and error messages
    notes = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.academy_name} - {self.plan_type.name} ({self.status})"
    
    def save(self, *args, **kwargs):
        """Override save to send notifications on status changes"""
        is_new = self.pk is None
        old_status = None
        
        if not is_new:
            try:
                old_instance = Subscription.objects.get(pk=self.pk)
                old_status = old_instance.status
            except Subscription.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
        
        # Send notifications for status changes
        if not is_new and old_status != self.status:
            self.send_status_notification()
    
    def send_status_notification(self):
        """Send email notification about subscription status"""
        try:
            subject = f"Subscription {self.get_status_display()} - {self.academy_name}"
            
            # Render email template
            context = {
                'subscription': self,
                'academy': {'name': self.academy_name},  # Create dict-like object for template
                'plan_type': self.plan_type,
                'status_display': self.get_status_display(),
                'payment_method_display': self.get_payment_method_display(),
            }
            
            html_message = render_to_string(
                'payment/emails/subscription_status.html',
                context
            )
            
            plain_message = render_to_string(
                'payment/emails/subscription_status.txt',
                context
            )
            
            # Send email to academy contact email
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[self.contact_email],
                html_message=html_message,
                fail_silently=False,
            )
            
            # Log successful email
            self.notes += f"\n[{timezone.now()}] Status notification email sent to {self.contact_email}"
            self.save(update_fields=['notes'])
            
        except Exception as e:
            # Log email failure
            self.notes += f"\n[{timezone.now()}] Failed to send notification email: {str(e)}"
            self.save(update_fields=['notes'])
    
    def send_invoice(self):
        """Send invoice email to academy"""
        try:
            subject = f"Invoice for {self.plan_type.name} - {self.academy_name}"
            
            # Render invoice template
            context = {
                'subscription': self,
                'academy': {'name': self.academy_name},  # Create dict-like object for template
                'plan_type': self.plan_type,
                'invoice_date': timezone.now().date(),
            }
            
            html_message = render_to_string(
                'payment/emails/invoice.html',
                context
            )
            
            plain_message = render_to_string(
                'payment/emails/invoice.txt',
                context
            )
            
            # Send email to academy contact email
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[self.contact_email],
                html_message=html_message,
                fail_silently=False,
            )
            
            # Log successful invoice email
            self.notes += f"\n[{timezone.now()}] Invoice email sent to {self.contact_email}"
            self.save(update_fields=['notes'])
            
        except Exception as e:
            # Log email failure
            self.notes += f"\n[{timezone.now()}] Failed to send invoice email: {str(e)}"
            self.save(update_fields=['notes'])
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Subscription"
        verbose_name_plural = "Subscriptions"
