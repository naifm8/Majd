from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from parents.models import Child
from .models import PlayerProfile
from academies.models import TrainingClass
from academies.models import SessionSkill


def player_dashboard_view(request, child_id):
    child = get_object_or_404(Child, id=child_id)
    player = getattr(child, "player_profile", None)

    if not player:
        return render(request, "player/dashboard.html", {
            "error": "No player profile found for this child."
        })

    # ✅ Skills progress
    if player.position:
        session_skills = SessionSkill.objects.filter(skill__position=player.position)
    else:
        session_skills = SessionSkill.objects.none()

    # ✅ 2. مهارات اللاعب الحالية
    player_skills = {ps.name: ps for ps in player.skills.all()}

    # ✅ 3. تجهيز المهارات للعرض
    skills_data = []
    for s_skill in session_skills:
        skill_name = s_skill.skill.name
        ps = player_skills.get(skill_name)
        skills_data.append({
            "name": skill_name,
            "current_level": ps.current_level if ps else 0,
            "target_level": ps.target_level if ps else s_skill.target_level,
            
        })

    skills_avg_progress = player.compute_skill_progress()


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
    
    opened_from = request.GET.get("from") or "parent"

    context = {
        "child": child,
        "player": player,
        "skills": skills_data,
        "skills_avg_progress": skills_avg_progress,   # من PlayerSkill
        "avg_progress": player.avg_progress,          # من Evaluations
        "grade": player.current_grade,                # الدرجة
        "next_class": next_class,
        "upcoming_classes": upcoming_classes,
        "attendances": attendances,
        "achievements": achievements,
        "evaluations": evaluations,
        "opened_from": opened_from,  # ✅ هذا هو السطر المطلوب
    }
    return render(request, "player/dashboard.html", context)
