# trainers/decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

# trainers/decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from accounts.models import TrainerProfile

def trainer_approved_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        u = request.user
        if not u.is_authenticated:
            return redirect("accounts:login_view")

        # اسمح للمشرفين دائماً (اختياري)
        if getattr(u, "is_superuser", False):
            return view_func(request, *args, **kwargs)

        if not u.groups.filter(name="trainer").exists():
            return redirect("accounts:login_view")

        tp = getattr(u, "trainer_profile", None)
        if not tp:
            messages.info(request, "أنشئ ملفك كمدرب أولاً.")
            return redirect("accounts:trainer_profile_view")

        status = tp.approval_status

        if status == TrainerProfile.ApprovalStatus.APPROVED:
            return view_func(request, *args, **kwargs)

        if status == TrainerProfile.ApprovalStatus.PENDING:
            messages.info(request, "Your account is under review by the academy.")
        elif status == TrainerProfile.ApprovalStatus.REJECTED:
            messages.error(request, "Your access has been rejected by the academy.")
        else:  # NotRegistered or any other unknown status
            messages.info(request, "Please complete your profile and submit it for review.")

        return redirect("accounts:trainer_profile_view")
    return _wrapped
