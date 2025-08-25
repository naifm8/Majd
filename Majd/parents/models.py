from django.db import models
from django.db.models.functions import ExtractYear, ExtractMonth, ExtractDay, Now
from django.db.models import IntegerField, Case, When, Value, Q, F

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