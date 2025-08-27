from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User, AcademyAdminProfile, TrainerProfile, ParentProfile

# Register your models here.

admin.site.register(AcademyAdminProfile)
admin.site.register(TrainerProfile)
admin.site.register(ParentProfile)
admin.site.register(Child)
