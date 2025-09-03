from django.db import models
from django.db.models.functions import ExtractYear, ExtractMonth, ExtractDay, Now
from django.db.models import IntegerField, Case, When, Value, Q, F
from academies.models import Program, Session, Academy
from accounts.models import ParentProfile
from cloudinary.models import CloudinaryField

# Create your models here.    

class ChildQuerySet(models.QuerySet):
    def with_age(self):
        return (
            self.alias(
                dob_year=ExtractYear("date_of_birth"),
                dob_month=ExtractMonth("date_of_birth"),
                dob_day=ExtractDay("date_of_birth"),
                today_year=ExtractYear(Now()),
                today_month=ExtractMonth(Now()),
                today_day=ExtractDay(Now()),
            )
            .annotate(
                age=Case(
                    When(date_of_birth__isnull=True, then=Value(None)),
                    default=F("today_year") - F("dob_year") - Case(
                        When(Q(dob_month__gt=F("today_month")) | (Q(dob_month=F("today_month")) & Q(dob_day__gt=F("today_day"))), then=1),
                        default=0,
                        output_field=IntegerField()
                    ),
                    output_field=IntegerField(),
                )
            )
        )



class Child(models.Model):
    class Gender(models.TextChoices):
        MALE   = "M", "Male"
        FEMALE = "F", "Female"

    class SkillLevel(models.TextChoices):
        BEGINNER     = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED     = "advanced", "Advanced"

    parent = models.ForeignKey(ParentProfile, on_delete=models.CASCADE, related_name='children')
    first_name = models.CharField(max_length=100)
    last_name  = models.CharField(max_length=100, blank=True)
    gender = models.CharField(max_length=1, choices=Gender.choices, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    primary_sport = models.CharField(max_length=100, blank=True)
    skill_level = models.CharField(max_length=20, choices=SkillLevel.choices, default=SkillLevel.BEGINNER, blank=True)
    medical_notes = models.TextField(blank=True, null=True)
    profile_image = CloudinaryField(
    'profile_image',
    folder='Majd/children/profile_images',
    blank=True,
    default='https://res.cloudinary.com/do1wotvij/image/upload/v1699999999/Majd/children/profile_images/default_profile.webp')
    objects = ChildQuerySet.as_manager()
    

    def __str__(self):
        full = f"{self.first_name} {self.last_name}".strip()
        return f"Child<{full} of {self.parent.user}>"
    

class Enrollment(models.Model):
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name="parent_enrollments")
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="enrollments")
    sessions = models.ManyToManyField(Session, blank=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    emergency_contact_name  = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)

    class Meta:
        unique_together = ("child", "program")

    def __str__(self):
        return f"{self.child.first_name} enrolled in {self.program.title} ({self.program.academy.name})"


class ParentSubscription(models.Model):
    """
    Track parent subscriptions to academies
    """
    parent = models.ForeignKey(ParentProfile, on_delete=models.CASCADE, related_name='subscriptions')
    academy = models.ForeignKey(Academy, on_delete=models.CASCADE, related_name='parent_subscriptions')
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    subscription_type = models.CharField(max_length=50, default='monthly')  # monthly, yearly, etc.
    amount_paid = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    class Meta:
        unique_together = ("parent", "academy")
    
    def __str__(self):
        return f"{self.parent.user.username} subscribed to {self.academy.name}"
    
    @property
    def is_expired(self):
        """Check if subscription has expired"""
        if self.end_date:
            from django.utils import timezone
            return timezone.now() > self.end_date
        return False
    
    @property
    def is_valid(self):
        """Check if subscription is valid (active and not expired)"""
        return self.is_active and not self.is_expired
    