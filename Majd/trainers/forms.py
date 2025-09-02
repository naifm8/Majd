from django import forms
from player.models import PlayerClassAttendance



class AttendanceForm(forms.Form):
    player_id = forms.IntegerField(widget=forms.HiddenInput())
    # الاسم لن نستخدمه للحفظ، فقط للعرض في الجدول
    player_name = forms.CharField(required=False, widget=forms.HiddenInput())

    status = forms.ChoiceField(
        choices=PlayerClassAttendance.Status.choices,
        widget=forms.Select(attrs={"class": "form-select form-select-sm"})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Note…"})
    )


SCALE_CHOICES = [(i, str(i)) for i in range(0, 6)]  # 0..5

class FocusSkillForm(forms.Form):
    """
    اختيار (اختياري) لمهارة تركيز واحدة على مستوى الكلاس.
    سنملأ الخيارات من SessionSkill.skill.name في الـ view.
    """
    skill_name = forms.ChoiceField(
        required=False,
        choices=[("", "— No focus skill —")],
        label="Focus Skill",
        widget=forms.Select(attrs={"class": "form-select"})
    )

SCALE_CHOICES = [(i, str(i)) for i in range(0, 6)]  # 0..5

class EvaluationRowForm(forms.Form):
    """
    فورم لصف واحد (طالب واحد) في التقييم.
    المهارات تُضاف ديناميكيًا من view.
    """
    player_id = forms.IntegerField(widget=forms.HiddenInput())

    # للمهارة المركزية (Focus Skill)
    skill_score = forms.ChoiceField(
        choices=SCALE_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-select form-select-sm"})
    )

    # ملاحظات عامة
    notes = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control form-control-sm",
            "placeholder": "Notes (optional)"
        })
    )