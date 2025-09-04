from django import forms
from .models import TrainerProfile
from academies.models import Academy

class TrainerProfileForm(forms.ModelForm):
    class Meta:
        model = TrainerProfile
        fields = [
            "certifications",
            "specialty",
            "years_of_experience",
            "position",
            "profile_image",
        ]
        widgets = {
            "certifications": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "specialty": forms.TextInput(attrs={"class": "form-control"}),
            "years_of_experience": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "position": forms.TextInput(attrs={"class": "form-control"}),
            "profile_image": forms.FileInput(attrs={"class": "form-control"}),

        }

class TrainerApplyForm(forms.Form):
    academy = forms.ModelChoiceField(
        queryset=Academy.objects.all(),
        widget=forms.Select(attrs={"class": "form-select"})
    )