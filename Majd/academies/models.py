from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from accounts.models import TrainerProfile, AcademyAdminProfile
from django.utils.text import slugify

class Academy(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, blank=True, null=True)
    logo = models.ImageField(upload_to="academies/logos/", blank=True, null=True)
    cover = models.ImageField(upload_to="academies/covers/", blank=True, null=True)
    description = models.TextField(max_length=500)
    city = models.CharField(max_length=80)
    email= models.CharField(max_length=50)
    latitude  = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    establishment_year = models.PositiveIntegerField(default=timezone.now().year, blank=True)
    owner = models.OneToOneField(AcademyAdminProfile,on_delete=models.CASCADE,related_name="academy")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)





class Program(models.Model):

    class SportType(models.TextChoices):
        FOOTBALL      = "football", "Football"
        BASKETBALL    = "basketball", "Basketball"
        VOLLEYBALL    = "volleyball", "Volleyball"
        TENNIS        = "tennis", "Tennis"
        TABLE_TENNIS  = "table_tennis", "Table Tennis"
        SWIMMING      = "swimming", "Swimming"

    academy = models.ForeignKey(Academy, on_delete=models.SET_NULL, null=True, blank=True, related_name="programs")
    title = models.CharField(max_length=120)
    short_description = models.TextField(max_length=300, blank=True)
    image = models.ImageField(upload_to="programs/", blank=True, null=True)
    sport_type = models.CharField(max_length=20, choices=SportType.choices, default=SportType.FOOTBALL)

    def age_group_display(self):
        sessions = self.sessions.all()
        if not sessions.exists():
            return None

        min_age = min(s.age_min for s in sessions)
        max_age = max(s.age_max for s in sessions)
        return f"{min_age}-{max_age} years"
    
    def __str__(self):
        academy_name = self.academy.name if self.academy else "❌ أكاديمية محذوفة"
        return f"{self.title} ({academy_name})"


class Session(models.Model):

    class Level(models.TextChoices):
        BEGINNER     = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED     = "advanced", "Advanced"

    class Gender(models.TextChoices):
        MALE   = "male", "Male"
        FEMALE = "female", "Female"
        MIX    = "mix", "Mix"

    program = models.ForeignKey("academies.Program", on_delete=models.CASCADE, related_name="sessions")
    title = models.CharField(max_length=120)
    trainer = models.ForeignKey("accounts.TrainerProfile", on_delete=models.SET_NULL, null=True, blank=True, related_name="sessions")
    age_min = models.PositiveIntegerField(default=6)
    age_max = models.PositiveIntegerField(default=16)
    gender = models.CharField(max_length=6, choices=Gender.choices, default=Gender.MIX)
    level = models.CharField(max_length=12, choices=Level.choices, default=Level.BEGINNER)
    capacity = models.PositiveIntegerField(default=20)
    enrolled = models.PositiveIntegerField(default=0)
    start_datetime = models.DateTimeField(null=True, blank=True)
    end_datetime   = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} - {self.program.title}"
    
    def duration_in_weeks(self):
        if self.start_datetime and self.end_datetime:
            delta = self.end_datetime.date() - self.start_datetime.date()
            weeks = delta.days // 7
            return max(1, weeks)  # at least 1 week
        return None

    def duration_display(self):
        weeks = self.duration_in_weeks()
        if not weeks:
            return "N/A"
        if weeks < 4:
            return f"{weeks} week{'s' if weeks > 1 else ''}"
        months = weeks // 4
        return f"{months} month{'s' if months > 1 else ''}"

    def generate_classes(self):
        from datetime import timedelta
        from .models import TrainingClass  # import داخلي عشان ما يصير circular import

        current_date = self.start_datetime.date()  # نحول datetime إلى date
        end_date = self.end_datetime.date()

        while current_date <= end_date:
            weekday_str = current_date.strftime("%a").lower()[:3]  # مثال: "mon"
            for slot in self.slots.all():
                if slot.weekday == weekday_str:
                    TrainingClass.objects.get_or_create(
                        session=self,
                        slot=slot,
                        date=current_date,
                        defaults={
                            "start_time": slot.start_time,
                            "end_time": slot.end_time,
                        }
                    )
            current_date += timedelta(days=1)

    def duration_weeks(self):
        if self.start_datetime and self.end_datetime:
            days = (self.end_datetime.date() - self.start_datetime.date()).days
            return max(1, days // 7)
        return None
            



class Position(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
    
    
class SkillDefinition(models.Model):
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name="skills")
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ("position", "name")

    def __str__(self):
        return f"{self.name} ({self.position.name})"
    
class SessionSkill(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="required_skills")
    skill = models.ForeignKey(SkillDefinition, on_delete=models.CASCADE)
    target_level = models.PositiveIntegerField(default=100)

    class Meta:
        unique_together = ("session", "skill")

    def __str__(self):
        return f"{self.skill.name} ({self.skill.position}) - {self.session}"


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
    weekday = models.CharField(max_length=10, choices=Weekday.choices)
    start_time = models.TimeField()
    end_time   = models.TimeField()
    
    
class TrainingClass(models.Model):
    session = models.ForeignKey("academies.Session", on_delete=models.CASCADE, related_name="classes")
    slot = models.ForeignKey("academies.SessionSlot", on_delete=models.SET_NULL, null=True, blank=True, related_name="classes")

    date = models.DateField()
    start_time = models.TimeField()   # منسوخة من slot وقت التوليد
    end_time   = models.TimeField()   # منسوخة من slot وقت التوليد

    topic = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ["date", "start_time"]  # ✅ يترتب تلقائي
        unique_together = ("session", "date", "start_time")  # ✅ يمنع التكرار

    def __str__(self):
        return f"{self.session.title} - {self.date} ({self.topic or 'General'})"
    
    
    
class PlanType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


# class SubscriptionPlan(models.Model):
#     academy = models.ForeignKey(
#         "academies.Academy",
#         on_delete=models.CASCADE,
#         related_name="plans"
#     )
#     name = models.CharField(max_length=100, default="Basic Plan")
#     price = models.DecimalField(max_digits=8, decimal_places=2)
#     duration_days = models.PositiveIntegerField(default=30)
#     description = models.TextField(blank=True)
#     is_active = models.BooleanField(default=True)

#     def __str__(self):
#         return f"{self.name} - {self.academy.name}"