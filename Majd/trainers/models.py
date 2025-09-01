from django.db import models
from django.conf import settings

from accounts.models import TrainerProfile
from academies.models import TrainingClass
from player.models import PlayerProfile


class ClassPlan(models.Model):
    STATUS_CHOICES = (("draft", "Draft"), ("published", "Published"))

    trainer = models.ForeignKey(TrainerProfile, on_delete=models.CASCADE, related_name="class_plans")
    training_class = models.OneToOneField(TrainingClass, on_delete=models.CASCADE, related_name="plan")

    title = models.CharField(max_length=200, blank=True)
    discretion = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="updated_class_plans")

    def __str__(self):
        return f"ClassPlan<{self.training_class}>"


class TrainingNote(models.Model):
    NOTE_TYPES = (
        ("general", "General"),
        ("behavior", "Behavior"),
        ("skill", "Skill"),
        ("medical", "Medical"),
        ("other", "Other"),
    )

    trainer = models.ForeignKey(TrainerProfile, on_delete=models.CASCADE, related_name="training_notes")
    training_class = models.ForeignKey(TrainingClass, on_delete=models.CASCADE, related_name="training_notes")
    player = models.ForeignKey(PlayerProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name="training_notes")

    note_type = models.CharField(max_length=20, choices=NOTE_TYPES, default="general")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        who = self.player or "All"
        return f"Note<{who} - {self.training_class.date}>"
