from django.shortcuts import render, redirect
from django.http import HttpResponse,HttpRequest
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Avg
from academies.models import TrainingClass
from player.models import PlayerProfile, PlayerSession, Achievement, Evaluation

# Create your views here.


# def overview_view(request:HttpRequest):

#     return render(request, "trainers/overview.html")



def get_today_and_now():
    today_date = timezone.localdate()
    now_datetime = timezone.localtime()
    return today_date, now_datetime


def get_week_bounds_start_sunday(today_date):
    weekday_index = today_date.weekday()              # Monday=0  Sunday=6
    week_start_date = today_date - timedelta(days=(weekday_index + 1) % 7)
    week_end_date = week_start_date + timedelta(days=6)
    return week_start_date, week_end_date


def format_time_12h(time_obj):
    return time_obj.strftime("%I:%M %p").lstrip("0")


def format_time_range(training_class):
    start_time_formatted = format_time_12h(training_class.start_time)
    end_time_formatted = format_time_12h(training_class.end_time)
    return f"{start_time_formatted} - {end_time_formatted}"


def get_status_label_and_css(now_datetime, training_class):
    tzinfo_obj = now_datetime.tzinfo
    start_datetime = datetime.combine(training_class.date, training_class.start_time, tzinfo=tzinfo_obj)
    end_datetime = datetime.combine(training_class.date, training_class.end_time, tzinfo=tzinfo_obj)

    if now_datetime < start_datetime:
        return "Upcoming", "bg-light text-secondary"
    elif start_datetime <= now_datetime < end_datetime:
        return "In Progress", "bg-success-subtle text-success"
    return "Completed", "bg-secondary-subtle text-secondary"


def calculate_weekly_hours(training_classes_queryset, now_datetime):
    tzinfo_obj = now_datetime.tzinfo
    total_seconds = 0
    for training_class in training_classes_queryset:
        start_datetime = datetime.combine(training_class.date, training_class.start_time, tzinfo=tzinfo_obj)
        end_datetime = datetime.combine(training_class.date, training_class.end_time, tzinfo=tzinfo_obj)
        diff_seconds = (end_datetime - start_datetime).total_seconds()
        if diff_seconds > 0:
            total_seconds += diff_seconds
    return round(total_seconds / 3600.0, 1)


def calculate_age(dob, today_date):
    if not dob:
        return None
    return today_date.year - dob.year - ((today_date.month, today_date.day) < (dob.month, dob.day))


def compute_improvement_percentage(player, trainer, now_datetime):

    current_window_start = now_datetime - timedelta(days=30)
    previous_window_start = now_datetime - timedelta(days=60)
    previous_window_end = now_datetime - timedelta(days=31)

    all_evaluations = Evaluation.objects.filter(player=player)
    evaluations_for_trainer = all_evaluations.filter(coach=trainer)
    evaluations = evaluations_for_trainer if evaluations_for_trainer.exists() else all_evaluations

    current_avg = evaluations.filter(created_at__gte=current_window_start).aggregate(avg=Avg("score"))["avg"] or 0.0
    previous_avg = evaluations.filter(
        created_at__gte=previous_window_start, created_at__lte=previous_window_end
    ).aggregate(avg=Avg("score"))["avg"] or 0.0

    if previous_avg <= 0:
        return 0.0
    return round(((current_avg - previous_avg) / previous_avg) * 100.0, 1)


def get_next_training_class_for_player(player, trainer, today_date):
    return (TrainingClass.objects.filter(session__player_sessions__player=player, session__trainer=trainer, date__gte=today_date).select_related("session").order_by("date", "start_time").first())



def overview_view(request:HttpRequest):
    user = request.user
    if not user.is_authenticated:
        return redirect("accounts:login_view")

    is_in_trainer_group = user.groups.filter(name="trainer").exists()
    has_trainer_profile = hasattr(user, "trainer_profile") and user.trainer_profile
    if not (is_in_trainer_group and has_trainer_profile):
        return redirect("accounts:login_view")

    trainer_profile = user.trainer_profile


    today_date, now_datetime = get_today_and_now()
    week_start_date, week_end_date = get_week_bounds_start_sunday(today_date)

    # ---------------------------------------------------
    # 1) Today's Sessions (TrainingClass لليوم)
    # ---------------------------------------------------
    todays_training_classes_queryset = (
        TrainingClass.objects
        .filter(session__trainer=trainer_profile, date=today_date)
        .select_related("session")
        .order_by("start_time")
    )

    # عدّ الطلاب لكل Session (من PlayerSession)
    session_ids = {training_class.session_id for training_class in todays_training_classes_queryset}
    students_per_session_dict = {
        session_id: PlayerSession.objects.filter(session_id=session_id).values("player").distinct().count()
        for session_id in session_ids
    }

    today_classes = []
    for training_class in todays_training_classes_queryset:
        status_label, status_css = get_status_label_and_css(now_datetime, training_class)
        today_classes.append({"title": training_class.session.title, "time_range": format_time_range(training_class), "students_count": students_per_session_dict.get(training_class.session_id, 0), "status_label": status_label, "status_css": status_css, "focus": training_class.topic or "", "start_url": "#", "edit_url": "#", "training_class_id": training_class.id,})
    today_classes_count = len(today_classes)

    # ---------------------------------------------------
    # 2) Summary Cards
    # ---------------------------------------------------
    training_classes_for_week_queryset = TrainingClass.objects.filter(session__trainer=trainer_profile, date__gte=week_start_date, date__lte=week_end_date)
    weekly_hours = calculate_weekly_hours(training_classes_for_week_queryset, now_datetime)

    students_count = (PlayerProfile.objects.filter(player_sessions__session__trainer=trainer_profile).distinct().count())

    # ---------------------------------------------------
    # 3) Recent Achievements (آخر 3)
    # ---------------------------------------------------
    achievements_queryset = (
        Achievement.objects
        .filter(player__player_sessions__session__trainer=trainer_profile)
        .select_related("player__child")
        .order_by("-date_awarded")
        .distinct()[:3]
    )
    achievements = [{
        "student_name": f"{achievement.player.child.first_name} {achievement.player.child.last_name}".strip(),
        "text": achievement.title if not achievement.description else f"{achievement.title} — {achievement.description}",
        "date": achievement.date_awarded,
    } for achievement in achievements_queryset]

    # ---------------------------------------------------
    # 4) Student Progress (Top 4)
    # ---------------------------------------------------
    players_queryset = (
        PlayerProfile.objects
        .filter(player_sessions__session__trainer=trainer_profile)
        .select_related("child", "position")
        .prefetch_related("player_sessions__session")
        .distinct()
        .order_by("-avg_progress")[:4]
    )

    student_progress = []
    for player in players_queryset:
        child = player.child
        student_name = f"{child.first_name} {child.last_name}".strip()
        avatar_initial = (child.first_name[:1] if child and child.first_name else "?").upper()

        # Track = عنوان أقرب/أحدث سيشن لهذا اللاعب مع نفس المدرّب (بشكل بسيط)
        sessions_for_trainer = [ps.session for ps in player.player_sessions.all() if ps.session and ps.session.trainer_id == trainer_profile.id]
        track_title = sessions_for_trainer[0].title if sessions_for_trainer else ""

        student_age = calculate_age(child.date_of_birth, today_date) if child else None
        attendance_percentage = round(player.attendance_rate or 0.0, 1)
        improvement_percentage = compute_improvement_percentage(player, trainer_profile, now_datetime)

        next_training_class = get_next_training_class_for_player(player, trainer_profile, today_date)
        if next_training_class:
            if next_training_class.date == today_date:
                next_session_label = f"Today {format_time_12h(next_training_class.start_time)}"
            else:
                next_session_label = f"{next_training_class.date.strftime('%A')} {format_time_12h(next_training_class.start_time)}"
        else:
            next_session_label = "—"

        student_progress.append({
            "initial": avatar_initial,
            "name": student_name,
            "age": student_age,
            "track": track_title,
            "attendance_pct": attendance_percentage,
            "improvement_pct": improvement_percentage,
            "next_session": next_session_label,
            "grade": player.current_grade or "",
        })

    # ---------------------------------------------------
    # 5) Template Context
    # ---------------------------------------------------
    context = {
        "trainer": {"name": user.get_full_name() or user.username,"academy_name": getattr(trainer_profile.academy, "name", ""), "specialty": trainer_profile.specialty, "students_count": students_count, "profile_image": getattr(trainer_profile, "profile_image", None)},
        "summary": {"today_classes_count": today_classes_count, "weekly_hours": weekly_hours, "students_count": students_count},
        "today_classes": today_classes, "achievements": achievements, "reminder": {"title": "Monthly evaluations due", "text": "Monthly evaluations for Elite Training students are due this Friday.", "url": "#"},
        "student_progress": student_progress,
    }
    return render(request, "trainers/overview.html", context)
