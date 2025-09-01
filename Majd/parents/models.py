from django.db import models
from django.db.models.functions import ExtractYear, ExtractMonth, ExtractDay, Now
from django.db.models import IntegerField, Case, When, Value, Q, F
from academies.models import Program
from accounts.models import ParentProfile

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
    programs = models.ManyToManyField(Program, related_name="children", blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    primary_sport = models.CharField(max_length=100, blank=True)
    skill_level = models.CharField(max_length=20, choices=SkillLevel.choices, default=SkillLevel.BEGINNER, blank=True)
    medical_notes = models.TextField(blank=True, null=True)
    profile_image = models.ImageField(upload_to="images/profileImage/", default="images/profileImage/profileImage.webp", blank=True)
    objects = ChildQuerySet.as_manager()

    def __str__(self):
        full = f"{self.first_name} {self.last_name}".strip()
        return f"Child<{full} of {self.parent.user}>"
    

class Enrollment(models.Model):
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name="parent_enrollments")
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="enrollments")
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    emergency_contact_name  = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)

    class Meta:
        unique_together = ("child", "program")

    def __str__(self):
        return f"{self.child.first_name} enrolled in {self.program.title} ({self.program.academy.name})"
    
    