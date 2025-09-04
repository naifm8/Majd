from django.db import models
from django.utils import timezone
from django.db.models import Avg
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from accounts.models import TrainerProfile
from parents.models import Child
from academies.models import Academy, Session, TrainingClass, Position, SessionSkill


class PlayerProfile(models.Model):
    child = models.OneToOneField(Child, on_delete=models.CASCADE, related_name="player_profile")
    academy = models.ForeignKey(Academy, on_delete=models.SET_NULL, null=True, blank=True, related_name="players")
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True, related_name="players")
    
    
    attendance_rate = models.FloatField(default=0)       
    current_grade   = models.CharField(max_length=5, blank=True)  
    avg_progress    = models.FloatField(default=0.0)      
    
    def compute_skill_progress(self):
        skills = self.skills.all()
        if not skills.exists():
            return 0.0
        total = sum(skill.current_level for skill in skills)
        return round(total / skills.count(), 1)

    def recompute_progress_and_grade(self):
        avg = self.evaluations.filter(skill__isnull=True).aggregate(avg=Avg("score"))["avg"] or 0.0
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
        try:
            return f"Player<{self.child.first_name} {self.child.last_name}>"
        except:
            return "❌ Broken PlayerProfile (Child not found)"



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
        avg = self.skill_evaluations.aggregate(avg=Avg("skill_score"))["avg"] or 0
        self.current_level = round(avg)
        self.save(update_fields=["current_level"])


class PlayerSession(models.Model):
    player = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name="player_sessions")
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="attendances")

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


class PlayerClassAttendance(models.Model):
    class Status(models.TextChoices):
        PRESENT  = "present", "Present"
        ABSENT   = "absent", "Absent"
        LATE     = "late", "Late"
        EXCUSED  = "excused", "Excused"

    player = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name="class_attendances")
    training_class = models.ForeignKey(TrainingClass, on_delete=models.CASCADE, related_name="attendances")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PRESENT)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ("player", "training_class")

    def __str__(self):
        return f"{self.player.child.first_name} - {self.training_class.date} ({self.status})"
    
    

class Evaluation(models.Model):
    player = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name="evaluations")
    coach  = models.ForeignKey(TrainerProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name="evaluations")
    training_class = models.ForeignKey(TrainingClass, on_delete=models.SET_NULL, null=True, blank=True, related_name="evaluations")


   
    skill = models.ForeignKey(PlayerSkill, on_delete=models.SET_NULL, null=True, blank=True, related_name="skill_evaluations")


    score = models.PositiveIntegerField(help_text="0-100")  
    skill_score = models.PositiveSmallIntegerField(null=True, blank=True)       
    performance_score = models.PositiveSmallIntegerField(null=True, blank=True) 
    feedback = models.TextField(blank=True)  
    notes = models.TextField(null=True, blank=True)  
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        who = f"{self.player.child.first_name} {self.player.child.last_name}"
        return f"Evaluation({who}, {self.training_class.date if self.training_class else 'N/A'}) - {self.score}"





@receiver([post_save, post_delete], sender=Evaluation)
def update_player_after_eval_change(sender, instance, **kwargs):

    instance.player.recompute_progress_and_grade()

    if instance.skill:
        instance.skill.update_from_evaluations()
        
        
        
        

@receiver([post_save, post_delete], sender=PlayerClassAttendance)
def update_player_attendance_rate(sender, instance, **kwargs):
    player = instance.player
    total = player.class_attendances.count()
    present_count = player.class_attendances.filter(
        status=PlayerClassAttendance.Status.PRESENT
    ).count()

    rate = (present_count / total) * 100 if total > 0 else 0
    player.attendance_rate = round(rate, 1)
    player.save(update_fields=["attendance_rate"])
    
    
    
@receiver(post_save, sender=PlayerSession)
def assign_skills_on_session_join(sender, instance, created, **kwargs):
    if not created:
        return

    player = instance.player
    session = instance.session

    if not player.position:
   
        return

    session_skills = SessionSkill.objects.filter(
        session=session,
        skill__position=player.position
    )

    for s_skill in session_skills:
        PlayerSkill.objects.get_or_create(
            player=player,
            name=s_skill.skill.name,
            defaults={
                "target_level": s_skill.target_level,
                "current_level": 0
            }
        )