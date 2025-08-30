# academies/forms.py
from django import forms
from .models import Academy, Program, Session, SessionSlot


class AcademyForm(forms.ModelForm):
    class Meta:
        model = Academy
        fields = ["logo", "cover", "description", "city", "establishment_year"]

class ProgramForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = ["title", "short_description", "image", "sport_type"]

class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = [
            "program", "title", "trainer",
            "age_min", "age_max", "gender", "level",
            "capacity", "start_date", "end_date"
        ]

class SessionSlotForm(forms.ModelForm):
    class Meta:
        model = SessionSlot
        fields = ["weekday", "start_time", "end_time"]
