from django.db import models

# Create your models here.
class ContactMessage(models.Model):

    INQUIRY_CHOICES = [
        ("general",  "General Inquiry"),
        ("partner",  "Partnership Opportunity"),
        ("sponsor",  "Sponsorship"),
        ("academy",  "Academy Registration"),
        ("tech",     "Technical Support"),
        ("media",    "Media & Press"),
    ]

    full_name   = models.CharField(max_length=120)
    email       = models.EmailField()
    organization= models.CharField(max_length=120, blank=True)
    phone       = models.CharField(max_length=20, blank=True)
    inquiry_type = models.CharField(
        max_length=20,
        choices=INQUIRY_CHOICES,
        default="general",
    )
    subject     = models.CharField(max_length=200)
    message     = models.TextField()
    created_at  = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.full_name} — {self.subject}"