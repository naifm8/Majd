from django.db import models
from accounts.models import Child
from academies.models import Session
# Create your models here.



class Evaluation(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    player = models.ForeignKey(Child, on_delete=models.CASCADE)
    skill_score = models.PositiveSmallIntegerField()
    performance_score = models.PositiveSmallIntegerField()
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Evaluation for {self.player} in {self.session}"


class attendance(models.Model):
    class Status(models.TextChoices):
        PRESENT = "present", "Present"
        ABSENT  = "absent",  "Absent"
        LATE    = "late",    "Late"
        EXCUSED = "excused", "Excused"
    
    session = models.ForeignKey("Session", on_delete=models.CASCADE, related_name="attendances")
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name="attendances")
    date = models.DateField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PRESENT)
    notes = models.TextField(blank=True)

