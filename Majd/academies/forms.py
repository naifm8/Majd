# academies/forms.py
from django import forms
from .models import Academy, Program, Session, SessionSlot
from payment.models import SubscriptionPlan
from accounts.models import TrainerProfile
from django.contrib.auth.models import User

class AcademyForm(forms.ModelForm):
    class Meta:
        model = Academy
        fields = [
            "logo",
            "cover",
            "description",
            "mission",
            "city",
            "establishment_year",
            "contact_number",
            "email",   
        ]

from django import forms
from .models import Session
from accounts.models import TrainerProfile

class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        exclude = ("program", "enrolled")  # 🚀 don't ask user for these
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "age_min": forms.NumberInput(attrs={"class": "form-control"}),
            "age_max": forms.NumberInput(attrs={"class": "form-control"}),
            "gender": forms.Select(attrs={"class": "form-select"}),
            "level": forms.Select(attrs={"class": "form-select"}),
            "capacity": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "start_datetime": forms.DateTimeInput(
                format="%Y-%m-%dT%H:%M",
                attrs={"type": "datetime-local", "class": "form-control"}
            ),
            "end_datetime": forms.DateTimeInput(
                format="%Y-%m-%dT%H:%M",
                attrs={"type": "datetime-local", "class": "form-control"}
            ),
        }

    def __init__(self, *args, academy=None, **kwargs):
        super().__init__(*args, **kwargs)
        # 🎯 limit trainers to academy
        if academy:
            self.fields["trainer"].queryset = TrainerProfile.objects.filter(academy=academy)
        else:
            self.fields["trainer"].queryset = TrainerProfile.objects.none()

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.enrolled is None:
            instance.enrolled = 0
        if commit:
            instance.save()
        return instance



class ProgramForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = ["title", "short_description", "image", "sport_type"]


class TrainerProfileForm(forms.ModelForm):
    trainer = forms.ModelChoiceField(
        queryset=TrainerProfile.objects.select_related("user", "academy").all(),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Trainer",
        empty_label="اختر مدرب"
    )

    class Meta:
        model = TrainerProfile
        fields = ["trainer", "certifications", "specialty", "years_of_experience", "position", "profile_image"]
        widgets = {
            "certifications": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "specialty": forms.TextInput(attrs={"class": "form-control"}),
            "years_of_experience": forms.NumberInput(attrs={"class": "form-control"}),
            "position": forms.TextInput(attrs={"class": "form-control"}),
            "profile_image": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }


class SubscriptionPlanForm(forms.ModelForm):
    class Meta:
        model = SubscriptionPlan
        fields = ["title", "price", "billing_type", "description", "is_active"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "billing_type": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, academy=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.academy = academy



# abdulaziz alkhateeb added this
class AdminTrainerDecisionForm(forms.Form):
    ACTION_CHOICES = (
        ("approve", "Approve"),
        ("reject", "Reject"),
    )
    trainer_id = forms.IntegerField(widget=forms.HiddenInput())
    action = forms.ChoiceField(choices=ACTION_CHOICES, widget=forms.HiddenInput())

    def clean_action(self):
        action = self.cleaned_data["action"]
        if action not in {"approve", "reject"}:
            raise forms.ValidationError("Invalid action.")
        return action