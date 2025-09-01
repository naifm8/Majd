from django import forms
from player.models import PlayerClassAttendance

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = PlayerClassAttendance
        fields = ["status", "notes"]
        widgets = {
            "status": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "notes": forms.Textarea(attrs={"class": "form-control form-control-sm", "rows": 1}),
        }
