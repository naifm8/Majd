from django.db import models
from django.contrib.auth.models import User
from django.conf import settings




class AcademyAdminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='academy_admin_profile')
    # academy = 

    def __str__(self):
        return f"AcademyAdmin<{self.user}>"


class TrainerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='trainer_profile')
    certifications = models.TextField(blank=True)
    specialty = models.CharField(max_length=100, blank=True)
    years_of_experience = models.PositiveIntegerField(null=True, blank=True)
    position= models.CharField(blank=True, max_length=100)
    profile_image = models.ImageField(upload_to="images/profileImage/", default="images/profileImage/profileImage.webp", blank=True
    )

    def __str__(self):
        return f"TrainerProfile<{self.user}>"


class ParentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='parent_profile')
    phone = models.CharField(max_length=12, blank=True,)
    latitude  = models.DecimalField(null=True, blank=True, decimal_places=15, max_digits=18)
    longitude = models.DecimalField(null=True, blank=True, decimal_places=15, max_digits=18)

    def __str__(self):
        return f"ParentProfile<{self.user}>"








