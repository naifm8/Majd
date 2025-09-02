# academies/forms.py
from django import forms
from .models import Academy, Program, Session, SessionSlot
from accounts.models import TrainerProfile
from django.contrib.auth.models import User
from payment.models import SubscriptionPlan, PlanType



class AcademyForm(forms.ModelForm):
    class Meta:
        model = Academy
        fields = ["logo", "cover", "description", "city", "establishment_year"]

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


class SubscriptionPlanForm(forms.ModelForm):
    class Meta:
        model = SubscriptionPlan
        fields = ['title', 'plan_type', 'price', 'billing_type', 'description', 'program_features', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 3-Month Training Plan, Elite Membership'}),
            'plan_type': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'billing_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'program_features': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter features separated by commas'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'title': 'Plan Title *',
            'plan_type': 'Plan Type (Optional)',
            'price': 'Price ($)',
            'billing_type': 'Billing Type',
            'description': 'Description',
            'program_features': 'Program Features (comma-separated)',
            'is_active': 'Active',
        }

    def __init__(self, *args, **kwargs):
        self.academy = kwargs.pop('academy', None)
        super().__init__(*args, **kwargs)
        # Make plan_type optional since it's now nullable
        self.fields['plan_type'].required = False
        self.fields['plan_type'].queryset = PlanType.objects.all()
        
        # Make title required (override model default)
        self.fields['title'].required = True
        
        # Convert program_features list to comma-separated string for display
        if self.instance and self.instance.pk and self.instance.program_features:
            if isinstance(self.instance.program_features, list):
                self.fields['program_features'].initial = ', '.join(self.instance.program_features)
        
    def clean_program_features(self):
        features_data = self.cleaned_data.get('program_features', '')
        
        # If it's already a list (from existing data), return as is
        if isinstance(features_data, list):
            return features_data
        
        # If it's a string (from form input), convert to list
        if isinstance(features_data, str) and features_data.strip():
            features_list = [feature.strip() for feature in features_data.split(',') if feature.strip()]
            return features_list
        
        return []
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        
        if title and self.academy:
            # Check for duplicate titles within the same academy
            queryset = SubscriptionPlan.objects.filter(academy=self.academy, title=title)
            
            # If editing an existing record, exclude it from the check
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise forms.ValidationError(f"A subscription plan with the title '{title}' already exists for this academy.")
        
        return title

