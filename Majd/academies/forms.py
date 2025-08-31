# academies/forms.py
from django import forms
from .models import Academy, Program, Session, SessionSlot
from accounts.models import TrainerProfile



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
        fields = "__all__"
        exclude = ("program",)
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "age_min": forms.NumberInput(attrs={"class": "form-control"}),
            "age_max": forms.NumberInput(attrs={"class": "form-control"}),
            "gender": forms.Select(attrs={"class": "form-select"}),
            "level": forms.Select(attrs={"class": "form-select"}),
            "capacity": forms.NumberInput(attrs={"class": "form-control"}),
            "start_datetime": forms.DateTimeInput(
                format="%Y-%m-%dT%H:%M",
                attrs={"type": "datetime-local", "class": "form-control"}
            ),
            "end_datetime": forms.DateTimeInput(
                format="%Y-%m-%dT%H:%M",
                attrs={"type": "datetime-local", "class": "form-control"}
            ),
        }

    def __init__(self, *args, **kwargs):
        academy = kwargs.pop("academy", None)  # pass academy from view
        super().__init__(*args, **kwargs)
        if academy:
            self.fields["trainer"].queryset = TrainerProfile.objects.filter(academy=academy)
        else:
            self.fields["trainer"].queryset = TrainerProfile.objects.none()


