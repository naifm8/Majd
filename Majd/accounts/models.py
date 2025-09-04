from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from cloudinary.models import CloudinaryField



class AcademyAdminProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='academy_admin_profile'
    )

    def __str__(self):
        return f"AcademyAdmin<{self.user}>"


class TrainerProfile(models.Model):
    class ApprovalStatus(models.TextChoices):
        PENDING  = "pending",  "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        NotRegistered = "NotRegistered", "Not Registered"

    user = models.OneToOneField( User, on_delete=models.SET_NULL, null=True, blank=True, related_name='trainer_profile')
    certifications = models.TextField(blank=True)
    specialty = models.CharField(max_length=100, blank=True)
    years_of_experience = models.PositiveIntegerField(null=True, blank=True)
    position= models.CharField(blank=True, max_length=100)
    profile_image = CloudinaryField(
    'profile_image',
    folder='Majd/trainers/profile_images',
    blank=True,
    default='https://res.cloudinary.com/do1wotvij/image/upload/v1699999999/Majd/trainers/profile_images/profileImage.webp')
    
    approval_status = models.CharField(max_length=50,choices=ApprovalStatus.choices, default=ApprovalStatus.NotRegistered, help_text="Academy approval status required for dashboard access.")
    academy = models.ForeignKey("academies.Academy", on_delete=models.SET_NULL, null=True, blank=True, related_name="trainers")
     
    def __str__(self):

        try:
            if self.user:
                full_name = f"{self.user.first_name} {self.user.last_name}".strip()
                if not full_name:
                    full_name = self.user.username
            else:
                full_name = "❌ محذوف"
        except:
            full_name = "❌ محذوف"


        try:
            academy_name = self.academy.name if self.academy else "❌ أكاديمية محذوفة"
        except:
            academy_name = "❌ أكاديمية محذوفة"

        return f"{full_name} ({academy_name})"


class ParentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='parent_profile')
    phone = models.CharField(max_length=12, blank=True,)
    location  = models.CharField(max_length=64,null=True, blank=True)
    

    def __str__(self):
        return f"ParentProfile<{self.user}>"
