from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models import IntegerField, Case, When, Value, Q, F
from django.db.models.functions import ExtractYear, ExtractMonth, ExtractDay, Now



class AcademyAdminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='academy_admin_profile')
    # academy = 

    def __str__(self):
        return f"AcademyAdmin<{self.user}>"


class TrainerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='trainer_profile')
    certifications = models.TextField(blank=True)
    specialty = models.CharField(max_length=100, blank=True)
    years_of_experience = models.PositiveIntegerField(null=True, blank=True)
    position= models.CharField(blank=True, max_length=100)
    profile_image = models.ImageField(upload_to="images/profileImage/", default="images/profileImage/profileImage.webp", blank=True
    )

    def __str__(self):
        return f"TrainerProfile<{self.user}>"


class ParentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='parent_profile')
    phone = models.CharField(max_length=12, blank=True,)
    latitude  = models.DecimalField(null=True, blank=True, decimal_places=15, max_digits=18)
    longitude = models.DecimalField(null=True, blank=True, decimal_places=15, max_digits=18)

    def __str__(self):
        return f"ParentProfile<{self.user}>"



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

    parent = models.ForeignKey(ParentProfile, on_delete=models.CASCADE, related_name='children')
    first_name = models.CharField(max_length=100)
    last_name  = models.CharField(max_length=100, blank=True)
    gender = models.CharField(max_length=1, choices=Gender.choices, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_image = models.ImageField(upload_to="images/profileImage/", default="images/profileImage/profileImage.webp", blank=True)
    objects = ChildQuerySet.as_manager()



    def __str__(self):
        full = f"{self.first_name} {self.last_name}".strip()
        return f"Child<{full} of {self.parent.user}>"
    
    
    class Meta:   # 👈 هنا نعدل الاسم
        verbose_name = "Child"
        verbose_name_plural = "Children"




