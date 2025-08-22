from django import forms
from .models import ContactMessage

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["full_name", "email", "organization", "phone", "inquiry_type", "subject", "message"]

        widgets = {
            "full_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter your full name"
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "Enter your email"
            }),
            "organization": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Academy, Club, Company"
            }),
            "phone": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "+966 XX XXX XXXX"
            }),
            "inquiry_type": forms.Select(attrs={
                "class": "form-select"
            }),
            "subject": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Brief subject of your inquiry"
            }),
            "message": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": "Please provide details about your inquiry..."
            }),
        }

