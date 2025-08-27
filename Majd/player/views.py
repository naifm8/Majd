from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from parents.models import Child
from .models import PlayerProfile
from academies.models import TrainingClass


def player_dashboard_view(request, child_id):
    child = get_object_or_404(Child, id=child_id)
    player = getattr(child, "player_profile", None)

    if not player:
        return render(request, "player/dashboard.html", {
            "error": "No player profile found for this child."
        })

    # ✅ Skills progress
    skills = player.skills.all()
    if skills.exists():
        total_progress = 0
        for skill in skills:
            if skill.target_level > 0:
                total_progress += (skill.current_level / skill.target_level) * 100
        skills_avg_progress = round(total_progress / skills.count(), 1)
    else:
        skills_avg_progress = 0

    # ✅ Evaluations history (على مستوى TrainingClass)
    evaluations = player.evaluations.select_related("coach", "training_class").all()

    # ✅ Next TrainingClass
    next_class = (TrainingClass.objects
                  .filter(session__in=player.player_sessions.values("session"),
                          date__gte=timezone.now().date())
                  .order_by("date", "start_time")
                  .first())

    # ✅ Upcoming TrainingClasses
    upcoming_classes = (TrainingClass.objects
                        .filter(session__in=player.player_sessions.values("session"),
                                date__gte=timezone.now().date())
                        .order_by("date", "start_time"))

    # ✅ Attendance records
    attendances = player.class_attendances.select_related("training_class").order_by("-training_class__date")

    # ✅ Achievements
    achievements = player.achievements.order_by("-date_awarded")[:5]

    context = {
        "child": child,
        "player": player,
        "skills": skills,
        "skills_avg_progress": skills_avg_progress,   # من PlayerSkill
        "avg_progress": player.avg_progress,          # من Evaluations
        "grade": player.current_grade,                # الدرجة
        "next_class": next_class,
        "upcoming_classes": upcoming_classes,
        "attendances": attendances,
        "achievements": achievements,
        "evaluations": evaluations,
    }
    return render(request, "player/dashboard.html", context)
