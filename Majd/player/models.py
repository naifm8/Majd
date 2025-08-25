from django.db import models
from django.utils import timezone
from django.db.models import Avg
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from accounts.models import Child, TrainerProfile


class PlayerProfile(models.Model):
    child = models.OneToOneField(Child, on_delete=models.CASCADE, related_name="player_profile")
    academy_name   = models.CharField(max_length=200, blank=True)
    attendance_rate = models.FloatField(default=0)         # 0..100
    current_grade   = models.CharField(max_length=5, blank=True)  
    avg_progress    = models.FloatField(default=0.0)       # متوسط درجات التقييمات (0..100)

    def recompute_progress_and_grade(self):
        """يحسب المتوسط والتقدير من التقييمات"""
        avg = self.evaluations.aggregate(avg=Avg("score"))["avg"] or 0.0
        self.avg_progress = round(avg, 2)

        if self.avg_progress >= 95:
            self.current_grade = "A+"
        elif self.avg_progress >= 90:
            self.current_grade = "A"
        elif self.avg_progress >= 85:
            self.current_grade = "B+"
        elif self.avg_progress >= 80:
            self.current_grade = "B"
        elif self.avg_progress >= 75:
            self.current_grade = "C+"
        elif self.avg_progress >= 70:
            self.current_grade = "C"
        elif self.avg_progress >= 60:
            self.current_grade = "D"
        else:
            self.current_grade = "F"

        self.save(update_fields=["avg_progress", "current_grade"])

    def __str__(self):
        return f"Player<{self.child.first_name} {self.child.last_name}>"


class PlayerSkill(models.Model):
    player = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name="skills")
    name = models.CharField(max_length=100)  
    current_level = models.PositiveIntegerField(default=0)
    target_level = models.PositiveIntegerField(default=100)

    class Meta:
        unique_together = ("player", "name")

    def __str__(self):
        return f"{self.player} - {self.name}"

    def update_from_evaluations(self):
        """يحدث مستوى المهارة من التقييمات المرتبطة"""
        avg = self.evaluations.aggregate(avg=Avg("score"))["avg"] or 0
        self.current_level = round(avg)
        self.save(update_fields=["current_level"])


class TrainingProgram(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class TrainingSession(models.Model):
    TRAINING = "training"
    ASSESSMENT = "assessment"
    TYPE_CHOICES = [(TRAINING, "Training"), (ASSESSMENT, "Assessment")]

    program = models.ForeignKey(
        TrainingProgram,
        on_delete=models.CASCADE,
        related_name="sessions",
        null=True, blank=True  
    )
    coach = models.ForeignKey(TrainerProfile, on_delete=models.SET_NULL, null=True, blank=True)
    start_at = models.DateTimeField()
    end_at   = models.DateTimeField()
    location = models.CharField(max_length=200, blank=True)
    focus    = models.CharField(max_length=200, blank=True)
    session_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TRAINING)

    def __str__(self):
        if self.program:
            return f"{self.program.name} @ {self.start_at:%Y-%m-%d %H:%M}"
        return f"Session @ {self.start_at:%Y-%m-%d %H:%M}"


class PlayerSession(models.Model):
    UPCOMING = "upcoming"
    ATTENDED = "attended"
    MISSED   = "missed"
    STATUS_CHOICES = [(UPCOMING, "Upcoming"), (ATTENDED, "Attended"), (MISSED, "Missed")]
    
    player = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name="player_sessions")
    session = models.ForeignKey(TrainingSession, on_delete=models.CASCADE, related_name="attendances")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=UPCOMING)
    remind_me = models.BooleanField(default=False)

    class Meta:
        unique_together = ("player", "session")

    def __str__(self):
        return f"{self.player} -> {self.session}"


class Achievement(models.Model):
    player = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name="achievements")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date_awarded = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.title} - {self.player}"


class Evaluation(models.Model):
    """تقييم الكوتش بعد كل Session"""
    player = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name="evaluations")
    coach  = models.ForeignKey(TrainerProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name="evaluations")
    session = models.ForeignKey(TrainingSession, on_delete=models.SET_NULL, null=True, blank=True, related_name="evaluations")

    # ✅ ربط التقييم بمهارة (اختياري)
    skill = models.ForeignKey(PlayerSkill, on_delete=models.SET_NULL, null=True, blank=True, related_name="evaluations")

    score = models.PositiveIntegerField(help_text="0-100")  # الدرجة
    feedback = models.TextField(blank=True)                 # ملاحظات
    created_at = models.DateTimeField(auto_now_add=True)    # التاريخ

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        who = f"{self.player.child.first_name} {self.player.child.last_name}"
        return f"Evaluation({who}, {self.score})"



# Signals لتحديث التقدير عند أي إضافة/تعديل/حذف تقييم
@receiver([post_save, post_delete], sender=Evaluation)
def update_player_after_eval_change(sender, instance, **kwargs):
    # تحديث متوسط اللاعب
    instance.player.recompute_progress_and_grade()
    # ✅ تحديث المهارة لو مربوطة
    if instance.skill:
        instance.skill.update_from_evaluations()