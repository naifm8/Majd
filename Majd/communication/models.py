from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from accounts.models import TrainerProfile, ParentProfile


class Conversation(models.Model):
    trainer = models.ForeignKey(TrainerProfile, on_delete=models.CASCADE, related_name='conversations')
    parent = models.ForeignKey(ParentProfile, on_delete=models.CASCADE, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('trainer', 'parent')

    def __str__(self):
        return f"{self.trainer.user.username} ↔ {self.parent.user.username}"


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)  # Either trainer.user or parent.user
    body = models.TextField()
    sent_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender.username}: {self.body[:30]}"
