from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from accounts.models import TrainerProfile, AcademyAdminProfile

# Create your models here.

class Academy(models.Model):
    name = models.CharField(max_length=120, unique=True)
    logo = models.ImageField(upload_to="academies/logos/", blank=True, null=True)
    cover = models.ImageField(upload_to="academies/covers/", blank=True, null=True)
    description = models.TextField(max_length=500)
    city = models.CharField(max_length=80)
    email= models.CharField(max_length=50)
    latitude  = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    establishment_year = models.PositiveIntegerField(default=timezone.now().year, blank=True)
    owner = models.OneToOneField(AcademyAdminProfile, on_delete=models.CASCADE, related_name="owned_academies")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name

# current_year = timezone.now().year
# academies = Academy.objects.annotate(
#     years_experience=Case(When(establishment_year__isnull=True, then=Value(None)), default=Value(current_year) - F("establishment_year"), output_field=IntegerField(),)
# )


class Program(models.Model):

    class SportType(models.TextChoices):
        FOOTBALL      = "football", "Football"
        BASKETBALL    = "basketball", "Basketball"
        VOLLEYBALL    = "volleyball", "Volleyball"
        TENNIS        = "tennis", "Tennis"
        TABLE_TENNIS  = "table_tennis", "Table Tennis"
        SWIMMING      = "swimming", "Swimming"

    academy = models.ForeignKey(Academy, on_delete=models.CASCADE, related_name="programs")
    title = models.CharField(max_length=120)
    short_description = models.CharField(max_length=200, blank=True)
    image = models.ImageField(upload_to="programs/", blank=True, null=True)
    sport_type = models.CharField(max_length=20, choices=SportType.choices, default=SportType.FOOTBALL)

    def __str__(self):
        return f"{self.title} ({self.get_sport_type_display()})"



class Session(models.Model):

    class Level(models.TextChoices):
        BEGINNER     = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED     = "advanced", "Advanced"

    class Gender(models.TextChoices):
        MALE   = "male", "Male"
        FEMALE = "female", "Female"
        MIX    = "mix", "Mix"

    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="sessions")
    title = models.CharField(max_length=120)
    trainer = models.ForeignKey(TrainerProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name="sessions")
    age_min = models.PositiveIntegerField(default=6)
    age_max = models.PositiveIntegerField(default=16)
    gender = models.CharField(max_length=6, choices=Gender.choices, default=Gender.MIX)
    level = models.CharField(max_length=12, choices=Level.choices, default=Level.BEGINNER)
    capacity = models.PositiveIntegerField(default=20)
    start_date = models.DateField()
    end_date   = models.DateField()

    def __str__(self):
        return f"{self.title} - {self.program.title}"



class SessionSlot(models.Model):
    class Weekday(models.TextChoices):
        SUNDAY    = "sun", "Sunday"
        MONDAY    = "mon", "Monday"
        TUESDAY   = "tue", "Tuesday"
        WEDNESDAY = "wed", "Wednesday"
        THURSDAY  = "thu", "Thursday"
        FRIDAY    = "fri", "Friday"
        SATURDAY  = "sat", "Saturday"

    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="slots")
    weekday = models.CharField(choices=Weekday.choices)
    start_time = models.TimeField()
    end_time   = models.TimeField()



# TODO later
# class AcademyPlan(models.Model):
#     academy = models.ForeignKey(Academy, on_delete=models.CASCADE, related_name="plans")
#     # TODO
#     # PlanType = models.ForeignKey(plan)
#     is_active = models.BooleanField(default=True)
#     duration_days = models.PositiveIntegerField(default=30)

#     def __str__(self): return f"{self.academy.name} - {self.name}"