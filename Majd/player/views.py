from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from accounts.models import Child
from .models import PlayerProfile


def player_dashboard_view(request, child_id):
    child = get_object_or_404(Child, id=child_id)
    player = getattr(child, "player_profile", None)

    if not player:
        return render(request, "player/dashboard.html", {
            "error": "No player profile found for this child."
        })

    # ✅ Skills progress (من PlayerSkill)
    skills = player.skills.all()
    if skills.exists():
        total_progress = 0
        for skill in skills:
            if skill.target_level > 0:
                total_progress += (skill.current_level / skill.target_level) * 100
        skills_avg_progress = round(total_progress / skills.count(), 1)
    else:
        skills_avg_progress = 0

    # ✅ Evaluations history
    evaluations = player.evaluations.select_related("coach", "session").all()

    # ✅ Sessions
    next_session = (player.player_sessions
                    .filter(session__start_at__gte=timezone.now())
                    .select_related("session", "session__coach")
                    .order_by("session__start_at")
                    .first())

    upcoming_sessions = (player.player_sessions
                         .filter(session__start_at__gte=timezone.now())
                         .select_related("session", "session__coach")
                         .order_by("session__start_at"))

    # ✅ Achievements
    achievements = player.achievements.order_by("-date_awarded")[:5]

    context = {
        "child": child,
        "player": player,
        "skills": skills,
        "skills_avg_progress": skills_avg_progress,   # التقدّم من الـ skills
        "avg_progress": player.avg_progress,          # المتوسط من التقييمات
        "grade": player.current_grade,                # الدرجة من التقييمات
        "next_session": next_session,
        "upcoming_sessions": upcoming_sessions,
        "achievements": achievements,
        "evaluations": evaluations,                   # نمرر التقييمات للـ tab
    }
    return render(request, "player/dashboard.html", context)
