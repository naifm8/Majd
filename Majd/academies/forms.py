# academies/forms.py
from django import forms
from .models import Academy

class AcademyForm(forms.ModelForm):
    class Meta:
        model = Academy
        fields = ["logo", "cover", "description", "city", "establishment_year"]
