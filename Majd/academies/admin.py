from django.contrib import admin
from .models import Academy, Program, Session, SessionSlot
# Register your models here.
admin.site.register(Academy)
admin.site.register(Program)
admin.site.register(Session)
admin.site.register(SessionSlot)