from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse,HttpRequest
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Avg, Q
from academies.models import TrainingClass, Session
from player.models import PlayerProfile, PlayerSession, Achievement, Evaluation, PlayerClassAttendance



# Create your views here.






def get_today_and_now():
    today_date = timezone.localdate()
    now_datetime = timezone.localtime()
    return today_date, now_datetime


def get_week_bounds_start_sunday(today_date):
    weekday_index = today_date.weekday()        
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


def get_next_training_class_for_player(player_profile, trainer, today_date):
    return (TrainingClass.objects.filter(session_id__in=PlayerSession.objects.filter(player=player_profile, session__trainer=trainer).values_list("session_id", flat=True), date__gte=today_date).select_related("session").order_by("date", "start_time").first())


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


    todays_training_classes_queryset = (
        TrainingClass.objects
        .filter(session__trainer=trainer_profile, date=today_date)
        .select_related("session")
        .order_by("start_time")
    )


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


    training_classes_for_week_queryset = TrainingClass.objects.filter(session__trainer=trainer_profile, date__gte=week_start_date, date__lte=week_end_date)
    weekly_hours = calculate_weekly_hours(training_classes_for_week_queryset, now_datetime)

    students_count = (PlayerProfile.objects.filter(player_sessions__session__trainer=trainer_profile).distinct().count())


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


    context = {
        "trainer": {"name": user.get_full_name() or user.username,"academy_name": getattr(trainer_profile.academy, "name", ""), "specialty": trainer_profile.specialty, "students_count": students_count, "profile_image": getattr(trainer_profile, "profile_image", None)},
        "summary": {"today_classes_count": today_classes_count, "weekly_hours": weekly_hours, "students_count": students_count},
        "today_classes": today_classes, "achievements": achievements, "reminder": {"title": "Monthly evaluations due", "text": "Monthly evaluations for Elite Training students are due this Friday.", "url": "#"},
        "student_progress": student_progress,
    }
    return render(request, "trainers/overview.html", context)


def students_view(request):

    user = request.user
    if not user.is_authenticated:
        return redirect("accounts:login_view")

    is_trainer_user = user.groups.filter(name="trainer").exists()
    trainer_profile = getattr(user, "trainer_profile", None)
    if not (is_trainer_user and trainer_profile):
        return redirect("accounts:login_view")


    search_query_string = (request.GET.get("query") or "").strip()
    view_mode_choice = (request.GET.get("view_mode") or "grid").lower()
    if view_mode_choice not in {"grid", "detail"}:
        view_mode_choice = "grid"
    selected_session_id_str = request.GET.get("selected_session_id") or None


    today_date, now_datetime = get_today_and_now()


    trainer_sessions_queryset = (
        Session.objects
        .filter(trainer=trainer_profile)
        .only("id", "title")
        .order_by("title")
    )

    students_count_by_session_id = {
        session_obj.id: PlayerSession.objects.filter(session=session_obj).values("player").distinct().count()
        for session_obj in trainer_sessions_queryset
    }

    total_assigned_students_count = (
        PlayerProfile.objects
        .filter(player_sessions__session__trainer=trainer_profile)
        .distinct()
        .count()
    )


    filter_chips = [{
        "label": "All Students",
        "count": total_assigned_students_count,
        "value": "",
        "active": not selected_session_id_str,
    }]
    for session_obj in trainer_sessions_queryset:
        filter_chips.append({
            "label": session_obj.title,
            "count": students_count_by_session_id.get(session_obj.id, 0),
            "value": str(session_obj.id),
            "active": selected_session_id_str == str(session_obj.id),
        })


    assigned_player_profiles_qs = (
        PlayerProfile.objects
        .filter(player_sessions__session__trainer=trainer_profile)
        .select_related("child", "position")
        .prefetch_related("player_sessions__session")
        .distinct()
    )

    if selected_session_id_str:
        assigned_player_profiles_qs = assigned_player_profiles_qs.filter(
            player_sessions__session_id=selected_session_id_str
        )

    if search_query_string:
        assigned_player_profiles_qs = assigned_player_profiles_qs.filter(
            Q(child__first_name__icontains=search_query_string) |
            Q(child__last_name__icontains=search_query_string)
        )


    student_items = []
    for player_profile in assigned_player_profiles_qs:
        child = player_profile.child
        full_name = f"{child.first_name} {child.last_name}".strip()
        avatar_initial = (child.first_name[:1] if child and child.first_name else "?").upper()


        sessions_for_this_trainer = [
            ps.session for ps in player_profile.player_sessions.all()
            if ps.session and ps.session.trainer_id == trainer_profile.id
        ]
        track_title = ""
        if selected_session_id_str:
            for s in sessions_for_this_trainer:
                if str(s.id) == selected_session_id_str:
                    track_title = s.title
                    break
        if not track_title and sessions_for_this_trainer:
            track_title = sessions_for_this_trainer[0].title


        if child and child.date_of_birth:
            age_years = (
                today_date.year - child.date_of_birth.year
                - ((today_date.month, today_date.day) < (child.date_of_birth.month, child.date_of_birth.day))
            )
        else:
            age_years = None


        attendance_percentage = round(player_profile.attendance_rate or 0.0, 1)  # 0..100
        overall_progress_percentage = round(player_profile.avg_progress or 0.0)  # 0..100
        improvement_percentage = compute_improvement_percentage(player_profile, trainer_profile, now_datetime)


        next_training_class = get_next_training_class_for_player(player_profile, trainer_profile, today_date)
        if next_training_class:
            if next_training_class.date == today_date:
                next_session_label = f"Today {format_time_12h(next_training_class.start_time)}"
            else:
                next_session_label = f"{next_training_class.date.strftime('%A')} {format_time_12h(next_training_class.start_time)}"
        else:
            next_session_label = "—"


        if age_years is not None and track_title:
            meta_text = f"Age {age_years} • {track_title}"
        elif age_years is not None:
            meta_text = f"Age {age_years}"
        else:
            meta_text = track_title

        student_items.append({
            "initial": avatar_initial,
            "name": full_name,
            "meta": meta_text,
            "overall_progress": overall_progress_percentage,
            "attendance_pct": attendance_percentage,
            "improvement_pct": improvement_percentage,
            "next_session": next_session_label,
            "grade": player_profile.current_grade or "",
            "profile_url": "#",
            "evaluate_url": "#",
        })


    context = {
        "trainer": {
            "name": user.get_full_name() or user.username,
            "academy_name": getattr(trainer_profile.academy, "name", ""),
            "specialty": trainer_profile.specialty,
            "profile_image": getattr(trainer_profile, "profile_image", None),
        },
        "filters": filter_chips,
        "students": student_items,
        "search_query": search_query_string,
        "current_filter": selected_session_id_str,    
        "view_mode": view_mode_choice,               
    }
    return render(request, "trainers/students.html", context)


def training_sessions_view(request: HttpRequest):

    user = request.user
    if not user.is_authenticated:
        return redirect("accounts:login_view")

    is_trainer_user = user.groups.filter(name="trainer").exists()
    trainer_profile = getattr(user, "trainer_profile", None)
    if not (is_trainer_user and trainer_profile):
        return redirect("accounts:login_view")


    active_tab = (request.GET.get("tab") or "today").lower()
    if active_tab not in {"today", "calendar", "upcoming"}:
        active_tab = "today"

    today_date, now_datetime = get_today_and_now()


    today_sessions = []
    if active_tab == "today" or not active_tab:
        today_qs = (
            TrainingClass.objects
            .filter(session__trainer=trainer_profile, date=today_date)
            .select_related("session")
            .order_by("start_time")
        )

        for training_class in today_qs:

            time_label = format_time_range(training_class)
            start_dt = datetime.combine(training_class.date, training_class.start_time, tzinfo=now_datetime.tzinfo)
            end_dt   = datetime.combine(training_class.date, training_class.end_time,   tzinfo=now_datetime.tzinfo)
            duration_minutes = max(0, int((end_dt - start_dt).total_seconds() // 60))


            status_label, status_css = get_status_label_and_css(now_datetime, training_class)
            status_tags = [{"label": status_label, "css": status_css}]


            assigned_count = PlayerSession.objects.filter(session=training_class.session).values("player").distinct().count()
            students_label = f"{assigned_count}/{training_class.session.capacity} students"


            attendance_records = (
                PlayerClassAttendance.objects
                .filter(training_class=training_class)
                .select_related("player__child")
                .order_by("player__child__first_name")
            )
            attendance_preview = []
            status_icon_map = {
                "present": "bi bi-check-circle",
                "late": "bi bi-clock-history",
                "absent": "bi bi-x-circle",
                "excused": "bi bi-exclamation-circle",
            }
            status_css_map = {
                "present": "text-success",
                "late": "text-warning",
                "absent": "text-danger",
                "excused": "text-secondary",
            }
            for rec in attendance_records[:4]:
                child = rec.player.child
                attendance_preview.append({
                    "name": f"{child.first_name} {child.last_name}".strip(),
                    "status_label": rec.get_status_display(),
                    "icon": status_icon_map.get(rec.status, "bi bi-clock"),
                    "status_css": status_css_map.get(rec.status, "text-muted"),
                })


            today_sessions.append({"id": training_class.id, "title": training_class.session.title, "time_label": time_label, "location_label": "—", "students_label": students_label, "duration_label": f"{duration_minutes} minutes", "status_tags": status_tags, "focus_text": training_class.topic or "", "equipment": [], "attendance_preview": attendance_preview, "attendance_checked": attendance_records.count(), "attendance_total": assigned_count, "start_url": "#", "edit_url": "#", "details_url": "#"})



    week_label = prev_week_start = next_week_start = week_start_str = None
    week_days = []
    if active_tab == "calendar":
        passed_week_start = request.GET.get("week_start")
        if passed_week_start:
            try:
                week_start_date = datetime.strptime(passed_week_start, "%Y-%m-%d").date()
            except ValueError:
                week_start_date, _ = get_week_bounds_start_sunday(today_date)
        else:
            week_start_date, _ = get_week_bounds_start_sunday(today_date)

        week_end_date = week_start_date + timedelta(days=6)
        week_start_str = week_start_date.isoformat()
        prev_week_start = (week_start_date - timedelta(days=7)).isoformat()
        next_week_start = (week_start_date + timedelta(days=7)).isoformat()

        if week_start_date.month == week_end_date.month:
            week_label = f"{week_start_date.strftime('%B %d')}–{week_end_date.strftime('%d, %Y')}"
        else:
            week_label = f"{week_start_date.strftime('%b %d')}–{week_end_date.strftime('%b %d, %Y')}"

        def level_color(level_code: str) -> str:
            mapping = {
                "beginner": "bg-success-subtle",
                "intermediate": "bg-info-subtle",
                "advanced": "bg-danger-subtle",
            }
            return mapping.get(level_code, "bg-light")

        for offset in range(7):
            day_date = week_start_date + timedelta(days=offset)
            day_classes = (
                TrainingClass.objects
                .filter(session__trainer=trainer_profile, date=day_date)
                .select_related("session")
                .order_by("start_time")
            )
            items = [{
                "title": cls.session.title,
                "time_label": format_time_12h(cls.start_time),
                "color_class": level_color(cls.session.level),
            } for cls in day_classes]

            week_days.append({
                "dow_label": day_date.strftime("%a"),
                "date_label": str(day_date.day),
                "items": items,
            })


    upcoming_sessions = []
    if active_tab == "upcoming":
        upcoming_qs = (
            TrainingClass.objects
            .filter(session__trainer=trainer_profile, date__gt=today_date)
            .select_related("session")
            .order_by("date", "start_time")
        )

        level_badge_css = {
            "beginner": "bg-success-subtle text-success",
            "intermediate": "bg-info-subtle text-info",
            "advanced": "bg-danger-subtle text-danger",
        }

        for training_class in upcoming_qs:
            assigned_count = PlayerSession.objects.filter(session=training_class.session).values("player").distinct().count()
            capacity = training_class.session.capacity
            upcoming_sessions.append({
                "month_short": training_class.date.strftime("%b"),
                "day_num": training_class.date.day,
                "title": training_class.session.title,
                "tag": {
                    "label": training_class.session.get_level_display(),
                    "css": level_badge_css.get(training_class.session.level, "bg-light text-secondary"),
                },
                "time_label": format_time_range(training_class),
                "location_label": "—",
                "students_label": f"{assigned_count}/{capacity}",
                "edit_url": "#",
                "details_url": "#",
            })


    context = {
        "active_tab": active_tab,


        "today_sessions": today_sessions,


        "week_label": week_label,
        "week_start": week_start_str,
        "prev_week_start": prev_week_start,
        "next_week_start": next_week_start,
        "week_days": week_days,


        "upcoming_sessions": upcoming_sessions,
    }
    return render(request, "trainers/training_sessions.html", context)


