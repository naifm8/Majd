from django import forms
from player.models import PlayerClassAttendance



class AttendanceForm(forms.Form):
    player_id = forms.IntegerField(widget=forms.HiddenInput())
  
    player_name = forms.CharField(required=False, widget=forms.HiddenInput())

    status = forms.ChoiceField(
        choices=PlayerClassAttendance.Status.choices,
        widget=forms.Select(attrs={"class": "form-select form-select-sm"})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Note…"})
    )

SCALE_0_5 = [(i, str(i)) for i in range(0, 6)]


class GeneralEvaluationRowForm(forms.Form):
    player_id = forms.IntegerField(widget=forms.HiddenInput())
    technique = forms.ChoiceField(choices=SCALE_0_5, initial=3, widget=forms.Select(attrs={"class": "form-select form-select-sm"}))
    tactical  = forms.ChoiceField(choices=SCALE_0_5, initial=3, widget=forms.Select(attrs={"class": "form-select form-select-sm"}))
    fitness   = forms.ChoiceField(choices=SCALE_0_5, initial=3, widget=forms.Select(attrs={"class": "form-select form-select-sm"}))
    mental    = forms.ChoiceField(choices=SCALE_0_5, initial=3, widget=forms.Select(attrs={"class": "form-select form-select-sm"}))
    notes     = forms.CharField(required=False, widget=forms.TextInput(attrs={"class":"form-control form-control-sm", "placeholder":"Notes (optional)"}))


class FocusSkillForm(forms.Form):
    skill_name = forms.ChoiceField(
        required=False,
        choices=[("", "— No focus skill —")],
        widget=forms.Select(attrs={"class": "form-select"})
    )

class SkillEvaluationRowForm(forms.Form):
    player_id   = forms.IntegerField(widget=forms.HiddenInput())
    skill_score = forms.ChoiceField(choices=SCALE_0_5, required=False, widget=forms.Select(attrs={"class":"form-select form-select-sm"}))
    notes       = forms.CharField(required=False, widget=forms.TextInput(attrs={"class":"form-control form-control-sm", "placeholder":"Notes (optional)"}))