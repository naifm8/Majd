from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse,HttpRequest
from datetime import datetime, timedelta
from datetime import date
from django.utils import timezone
from django.contrib.auth.models import User
from accounts.models import TrainerProfile
from django.db.models import Avg, Max, Min, Q
from academies.models import TrainingClass, Session, SessionSkill
from player.models import PlayerProfile, PlayerSession, Achievement, Evaluation, PlayerClassAttendance
from django.urls import reverse

from django import forms
from django.forms import formset_factory
from django.contrib import messages

from .forms import AttendanceForm, FocusSkillForm, EvaluationRowForm


# Create your views here.




# utilty
def compute_weighted_score(tech, tac, fit, mental, scale=5):

    t = int(tech); q = int(tac); f = int(fit); m = int(mental)
    total = (0.40 * (t/scale) + 0.30 * (q/scale) + 0.20 * (f/scale) + 0.10 * (m/scale)) * 100.0
    return round(total)

def class_eval_stats(training_class):

    qs = Evaluation.objects.filter(training_class=training_class)
    enrolled = PlayerSession.objects.filter(session=training_class.session).values("player").distinct().count()
    
    rated    = qs.values("player").distinct().count()
    agg      = qs.aggregate(avg=Avg("score"), mx=Max("score"), mn=Min("score"))
    return {
        "enrolled": enrolled,
        "rated": rated,
        "coverage_pct": round((rated/enrolled)*100, 1) if enrolled else 0.0,
        "avg": round(agg["avg"]) if agg["avg"] is not None else None,
        "max": agg["mx"],
        "min": agg["mn"],
        "not_rated": max(0, enrolled - rated),
    }

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




# view

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
            "profile_url": reverse("player:player_dashboard_view", args=[player_profile.child.id]) + "?from=trainer",
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
            week_label = f"{week_start_date.strftime('%B %d')}-{week_end_date.strftime('%d, %Y')}"
        else:
            week_label = f"{week_start_date.strftime('%b %d')}-{week_end_date.strftime('%b %d, %Y')}"

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


def attendance_view(request: HttpRequest):
    user = request.user
    if not user.is_authenticated:
        return redirect("accounts:login_view")

    trainer_profile = getattr(user, "trainer_profile", None)
    if not trainer_profile:
        return redirect("accounts:login_view")


    today_date, now_dt = get_today_and_now()


    today_att_qs = PlayerClassAttendance.objects.filter(
        training_class__session__trainer=trainer_profile,
        training_class__date=today_date,
    )
    today_total_records = today_att_qs.count()
    today_present_records = today_att_qs.filter(
        status=PlayerClassAttendance.Status.PRESENT
    ).count()
    today_attendance_pct = round(
        (today_present_records / today_total_records) * 100, 1
    ) if today_total_records else 0.0

    all_att_qs = PlayerClassAttendance.objects.filter(
        training_class__session__trainer=trainer_profile
    )
    all_total_records = all_att_qs.count()
    all_present_records = all_att_qs.filter(
        status=PlayerClassAttendance.Status.PRESENT
    ).count()
    avg_attendance_pct = round(
        (all_present_records / all_total_records) * 100, 1
    ) if all_total_records else 0.0

    completed_sessions_count = (
        all_att_qs.values("training_class").distinct().count()
    )

    total_classes_count = TrainingClass.objects.filter(
        session__trainer=trainer_profile
    ).count()

    stats = {
        "today_attendance_pct": today_attendance_pct,
        "today_present": today_present_records,
        "today_total": today_total_records,
        "avg_attendance_pct": avg_attendance_pct,
        "completed_sessions": completed_sessions_count,
        "active_classes": total_classes_count,
    }


    filter_session = request.GET.get("filter_session", "all")
    filter_date_str = request.GET.get("filter_date") 
    student_query = (request.GET.get("q") or "").strip()
    expanded_class_id = request.GET.get("expand")  

    trainer_sessions = (
        Session.objects
        .filter(trainer=trainer_profile)
        .order_by("title")
        .values("id", "title")
    )


    classes_qs = (
        TrainingClass.objects
        .filter(session__trainer=trainer_profile)
        .select_related("session")
        .order_by("date", "start_time")
    )

    if filter_session and filter_session != "all":
        try:
            filter_session_id = int(filter_session)
            classes_qs = classes_qs.filter(session_id=filter_session_id)
        except (TypeError, ValueError):
            pass 

    selected_date = None
    if filter_date_str:
        try:
            selected_date = date.fromisoformat(filter_date_str)
            classes_qs = classes_qs.filter(date=selected_date)
        except ValueError:
            selected_date = None

    if student_query:
        classes_qs = classes_qs.filter(
            Q(session__attendances__player__child__first_name__icontains=student_query) |
            Q(session__attendances__player__child__last_name__icontains=student_query)
        ).distinct()


    class_cards = []
    for training_class in classes_qs:
        status_label, status_css = get_status_label_and_css(now_dt, training_class)

        enrolled_count = (
            PlayerSession.objects
            .filter(session=training_class.session)
            .values("player").distinct().count()
        )
        capacity = training_class.session.capacity

        att_qs = (
            PlayerClassAttendance.objects
            .filter(training_class=training_class)
            .select_related("player__child")
            .order_by("player__child__first_name", "player__child__last_name")
        )
        present_count = att_qs.filter(status=PlayerClassAttendance.Status.PRESENT).count()
        absent_count = att_qs.filter(status=PlayerClassAttendance.Status.ABSENT).count()

        total_marked = present_count + absent_count + \
            att_qs.filter(status__in=[
                PlayerClassAttendance.Status.LATE,
                PlayerClassAttendance.Status.EXCUSED
            ]).count()
        attendance_pct_for_card = round(
            (present_count / total_marked) * 100, 1
        ) if total_marked else None  

        is_expanded = str(training_class.id) == str(expanded_class_id)

        attendance_details = []
        if is_expanded and att_qs.exists():
            status_css_map = {
                PlayerClassAttendance.Status.PRESENT: "text-success",
                PlayerClassAttendance.Status.ABSENT: "text-danger",
                PlayerClassAttendance.Status.LATE: "text-warning",
                PlayerClassAttendance.Status.EXCUSED: "text-secondary",
            }
            for rec in att_qs:
                child = rec.player.child
                full_name = f"{child.first_name} {child.last_name}".strip()
                attendance_details.append({
                    "name": full_name,
                    "status_label": rec.get_status_display(),
                    "status_css": status_css_map.get(rec.status, "text-muted"),
                    "note": (rec.notes or "").strip(),
                })

        class_cards.append({
            "id": training_class.id,
            "title": training_class.session.title,
            "date_label": str(training_class.date),
            "time_label": format_time_range(training_class),
            "location_label": "—",
            "status_label": status_label,
            "status_css": status_css,
            "attendance_pct": attendance_pct_for_card,
            "present": present_count,
            "absent": absent_count,
            "enrolled": enrolled_count,
            "capacity": capacity,
            "take_url_name": "trainers:take_attendance", 
            "is_expanded": is_expanded,
            "attendance_details": attendance_details, 
        })


    context = {
        "stats": {
            "today_attendance_pct": stats["today_attendance_pct"],
            "today_present": stats["today_present"],
            "today_total": stats["today_total"],
            "avg_attendance_pct": stats["avg_attendance_pct"],
            "completed_sessions": stats["completed_sessions"],
            "active_classes": stats["active_classes"],
        },

        "filter_options": {
            "sessions": list(trainer_sessions),  
            "selected_session": filter_session,   
            "selected_date": filter_date_str or "",
            "student_query": student_query,
        },

        "class_cards": class_cards,
    }

    return render(request, "trainers/attendance_dashboard.html", context)


def take_attendance_view(request, class_id: int):
    # تأكيد صلاحية المدرّب
    user = request.user
    if not user.is_authenticated:
        return redirect("accounts:login_view")
    trainer = getattr(user, "trainer_profile", None)
    if not trainer:
        return redirect("accounts:login_view")

    training_class = get_object_or_404(
        TrainingClass.objects.select_related("session"),
        pk=class_id
    )
    # حظر الوصول على كلاس لمدرب آخر
    if training_class.session.trainer_id != trainer.id:
        return redirect("trainers:attendance_view")

    # لاعبو هذا الكلاس (المسجّلون في Session)
    enrolled = (
        PlayerSession.objects
        .filter(session=training_class.session)
        .select_related("player__child")
    )

    # سجلات الحضور الحالية
    existing_att = (
        PlayerClassAttendance.objects
        .filter(training_class=training_class)
        .select_related("player__child")
    )
    existing_by_player = {a.player_id: a for a in existing_att}

    # نبني initial لكل لاعب (اتحاد المسجلين + الموجودين في الحضور)
    player_items = {}
    for ps in enrolled:
        child = getattr(ps.player, "child", None)
        name = f"{child.first_name} {child.last_name}".strip() if child else "—"
        player_items[ps.player_id] = {
            "player_id": ps.player_id,
            "player_name": name,
        }
    for a in existing_att:
        # لو فيه لاعب بس في الحضور (نادر)، برضه نعرضه
        if a.player_id not in player_items:
            child = getattr(a.player, "child", None)
            name = f"{child.first_name} {child.last_name}".strip() if child else "—"
            player_items[a.player_id] = {
                "player_id": a.player_id,
                "player_name": name,
            }

    # ترتيب أبجدي بالاسم
    initial_list = []
    for pid, item in sorted(player_items.items(), key=lambda kv: kv[1]["player_name"].lower()):
        existing = existing_by_player.get(pid)
        initial_list.append({
            "player_id": pid,
            "player_name": item["player_name"],
            "status": existing.status if existing else PlayerClassAttendance.Status.PRESENT,
            "notes": (existing.notes or "") if existing else "",
        })

    AttendanceFormSet = formset_factory(AttendanceForm, extra=0)
    if request.method == "POST":
        formset = AttendanceFormSet(request.POST)
        if formset.is_valid():
            saved = 0
            for f in formset:
                pid = f.cleaned_data["player_id"]
                status = f.cleaned_data["status"]
                notes = f.cleaned_data.get("notes") or ""
                obj, created = PlayerClassAttendance.objects.get_or_create(
                    training_class=training_class,
                    player_id=pid,
                    defaults={"status": status, "notes": notes},
                )
                if not created:
                    changed = (obj.status != status) or ((obj.notes or "") != notes)
                    if changed:
                        obj.status = status
                        obj.notes = notes
                        obj.save()
                saved += 1
            messages.success(request, "Attendance saved.")
            # يرجّعك للوحة الحضور
            return redirect("trainers:attendance_view")
    else:
        formset = AttendanceFormSet(initial=initial_list)

    # ملخّص صغير للكلاس
    today_date, now_dt = get_today_and_now()
    status_label, status_css = get_status_label_and_css(now_dt, training_class)

    # أرقام سريعة
    present_like = [PlayerClassAttendance.Status.PRESENT, PlayerClassAttendance.Status.LATE]
    present_count = existing_att.filter(status__in=present_like).count()
    absent_count = existing_att.filter(status__in=[PlayerClassAttendance.Status.ABSENT,
                                                   PlayerClassAttendance.Status.EXCUSED]).count()

    enrolled_count = enrolled.values("player").distinct().count()
    capacity = training_class.session.capacity

    context = {
        "class_info": {
            "id": training_class.id,
            "title": training_class.session.title,
            "date_label": training_class.date.strftime("%b %d, %Y"),
            "time_label": format_time_range(training_class),
            "status_label": status_label,
            "status_css": status_css,
            "enrolled": enrolled_count,
            "capacity": capacity,
        },
        "formset": formset,
    }
    return render(request, "trainers/take_attendance.html", context)


def evaluations_view(request: HttpRequest):
    user = request.user
    if not user.is_authenticated:
        return redirect("accounts:login_view")

    trainer_profile = getattr(user, "trainer_profile", None)
    if not trainer_profile:
        return redirect("accounts:login_view")

    filter_session = request.GET.get("filter_session", "all")
    filter_date    = request.GET.get("filter_date") or ""
    student_query  = (request.GET.get("q") or "").strip()
    active_view    = (request.GET.get("view") or "classes").lower()
    if active_view not in {"classes","students"}:
        active_view = "classes"
    expanded_class_id = request.GET.get("expand")

    trainer_sessions = Session.objects.filter(trainer=trainer_profile).order_by("title").values("id","title")

    classes_qs = TrainingClass.objects.filter(session__trainer=trainer_profile).select_related("session").order_by("date","start_time")
    if filter_session != "all":
        try:
            classes_qs = classes_qs.filter(session_id=int(filter_session))
        except:
            pass
    if filter_date:
        from datetime import date as _date
        try:
            classes_qs = classes_qs.filter(date=_date.fromisoformat(filter_date))
        except:
            pass

    today_date, now_dt = get_today_and_now()
    month_start = today_date.replace(day=1)
    month_evals = Evaluation.objects.filter(coach=trainer_profile, created_at__date__gte=month_start)
    kpi_total   = month_evals.count()
    kpi_avg     = round(month_evals.aggregate(a=Avg("score"))["a"]) if kpi_total else None

    assigned_players = PlayerProfile.objects.filter(player_sessions__session__trainer=trainer_profile).distinct()[:200]
    improving = 0
    for p in assigned_players:
        imp = compute_improvement_percentage(p, trainer_profile, now_dt)
        if imp >= 5.0:
            improving += 1

    month_classes = classes_qs.filter(date__gte=month_start, date__lte=today_date)
    pending = 0
    for cls in month_classes:
        st = class_eval_stats(cls)
        if st["enrolled"] and st["rated"] < st["enrolled"]:
            pending += 1

    class_cards = []
    for cls in classes_qs:
        status_label, status_css = get_status_label_and_css(now_dt, cls)
        st = class_eval_stats(cls)

        expanded_items = []
        if expanded_class_id and str(expanded_class_id) == str(cls.id):
            enrolled = PlayerSession.objects.filter(session=cls.session).select_related("player__child")
            evals_by_player = {e.player_id: e for e in Evaluation.objects.filter(training_class=cls).select_related("player__child")}
            for ps in enrolled:
                child = ps.player.child
                name = f"{child.first_name} {child.last_name}".strip() if child else "—"
                ev   = evals_by_player.get(ps.player_id)
                expanded_items.append({
                    "name": name,
                    "score": ev.score if ev else None,
                    "has_notes": bool(ev and (ev.feedback or ev.notes)),
                })

        class_cards.append({
            "id": cls.id,
            "title": cls.session.title,
            "date_label": str(cls.date),
            "time_label": format_time_range(cls),
            "status_label": status_label,
            "status_css": status_css,
            "coverage_pct": st["coverage_pct"],
            "enrolled": st["enrolled"],
            "rated": st["rated"],
            "avg": st["avg"],
            "max": st["max"],
            "min": st["min"],
            "not_rated": st["not_rated"],
            "expanded": (str(expanded_class_id) == str(cls.id)),
            "expanded_items": expanded_items,
        })

    student_cards = []
    if active_view == "students":
        students_qs = PlayerProfile.objects.filter(player_sessions__session__trainer=trainer_profile).select_related("child").distinct()
        if filter_session != "all":
            students_qs = students_qs.filter(player_sessions__session_id=filter_session)
        if student_query:
            students_qs = students_qs.filter(
                Q(child__first_name__icontains=student_query) |
                Q(child__last_name__icontains=student_query)
            )

        for p in students_qs[:40]:
            child = p.child
            name  = f"{child.first_name} {child.last_name}".strip() if child else "—"
            last_ev = Evaluation.objects.filter(player=p).order_by("-created_at").first()
            last_score = last_ev.score if last_ev else None
            imp = compute_improvement_percentage(p, trainer_profile, now_dt)
            nxt = get_next_training_class_for_player(p, trainer_profile, today_date)
            if nxt:
                next_label = f"{'Today' if nxt.date==today_date else nxt.date.strftime('%a')} {format_time_12h(nxt.start_time)}"
            else:
                next_label = "—"
            student_cards.append({
                "name": name,
                "initial": (child.first_name[:1] if child and child.first_name else "?").upper(),
                "track": p.player_sessions.first().session.title if p.player_sessions.first() else "",
                "last_score": last_score,
                "delta": imp,
                "next_label": next_label,
                "player_id": p.id,
            })

    context = {
        "kpi": {
            "total": kpi_total,
            "average": kpi_avg,
            "improving": improving,
            "pending": pending,
        },
        "filter_options": {
            "sessions": list(trainer_sessions),
            "selected_session": filter_session,
            "selected_date": filter_date,
            "student_query": student_query,
            "active_view": active_view,
        },
        "class_cards": class_cards,
        "student_cards": student_cards,
    }
    return render(request, "trainers/evaluations_dashboard.html", context)


def take_evaluations_view(request: HttpRequest, class_id: int):
    user = request.user
    if not user.is_authenticated:
        return redirect("accounts:login_view")

    trainer = getattr(user, "trainer_profile", None)
    if not trainer:
        return redirect("accounts:login_view")

    training_class = get_object_or_404(
        TrainingClass.objects.select_related("session"), pk=class_id
    )
    if training_class.session.trainer_id != trainer.id:
        return redirect("trainers:evaluations_view")

    # الطلاب المسجلين في الجلسة
    enrolled = PlayerSession.objects.filter(
        session=training_class.session
    ).select_related("player__child")

    # المهارات المناسبة لكل طالب حسب مركزه
    player_skill_map = {}
    for ps in enrolled:
        player = ps.player
        position = player.position

        if not position:
            player_skill_map[player.id] = []
            continue

        session_skills = SessionSkill.objects.filter(
            session=training_class.session,
            skill__position=position
        ).select_related("skill")
        player_skill_map[player.id] = list(session_skills)

    # التقييمات السابقة للكلاس
    existing_qs = Evaluation.objects.filter(training_class=training_class).select_related("player__child")
    existing_by_player = {e.player_id: e for e in existing_qs}

    # جميع أسماء المهارات (لـ Focus Skill)
    session_skill_names = list(
        SessionSkill.objects.filter(session=training_class.session)
        .select_related("skill", "skill__position")
        .values_list("skill__name", flat=True)
        .distinct()
    )

    # إعداد الفورم والديناميكية
    from django.forms import ChoiceField, Select
    SCALE_CHOICES = [(i, str(i)) for i in range(0, 6)]

    # 🔁 نحسب عدد المهارات الأعلى بين الطلاب
    max_skills_count = max(len(skills) for skills in player_skill_map.values())

    # 🔧 نضيف الحقول إلى EvaluationRowForm (مرة واحدة فقط)
    for i in range(max_skills_count):
        field_name = f"skill_{i}"
        EvaluationRowForm.base_fields[field_name] = ChoiceField(
            choices=SCALE_CHOICES,
            required=False,
            widget=Select(attrs={"class": "form-select form-select-sm"})
        )


    FocusForm = FocusSkillForm
    EvaluationFormSet = formset_factory(EvaluationRowForm, extra=0)

    # إعداد البيانات الابتدائية
    initial_rows = []
    name_by_player = {}
    for ps in enrolled:
        child = ps.player.child
        name = f"{child.first_name} {child.last_name}".strip() if child else "—"
        name_by_player[ps.player_id] = name

    for e in existing_qs:
        if e.player_id not in name_by_player:
            child = e.player.child
            name_by_player[e.player_id] = f"{child.first_name} {child.last_name}".strip() if child else "—"

    for pid, pname in sorted(name_by_player.items(), key=lambda kv: kv[1].lower()):
        skills = player_skill_map.get(pid, [])
        skill_fields = {f"skill_{i}": "" for i in range(len(skills))}
        initial_rows.append({
            "player_id": pid,
            "notes": (existing_by_player.get(pid).feedback or existing_by_player.get(pid).notes)
            if existing_by_player.get(pid) else "",
            **skill_fields
        })

    # POST: معالجة التقييمات
    if request.method == "POST":
        focus_form = FocusForm(request.POST)
        focus_form.fields["skill_name"].choices = [("", "— No focus skill —")] + [(n, n) for n in session_skill_names]
        formset = EvaluationFormSet(request.POST)

        if focus_form.is_valid() and formset.is_valid():
            saved = 0
            for f in formset:
                cd = f.cleaned_data
                pid = cd["player_id"]
                notes = cd.get("notes") or ""
                skills = player_skill_map.get(pid, [])

                for i, session_skill in enumerate(skills):
                    score_field = f"skill_{i}"
                    raw_score = cd.get(score_field)
                    if raw_score in ("", None):
                        continue

                    # نحاول نربط بـ PlayerSkill
                    pskill = PlayerSkill.objects.filter(player_id=pid, name=session_skill.skill.name).first()
                    if not pskill:
                        continue

                    Evaluation.objects.update_or_create(
                        player_id=pid,
                        training_class=training_class,
                        skill=pskill,
                        defaults={
                            "coach": trainer,
                            "score": int(raw_score),
                            "skill_score": int(raw_score),
                            "feedback": notes,
                        }
                    )

                saved += 1

            messages.success(request, f"✅ Evaluations saved for {saved} students.")
            return redirect("trainers:evaluations_view")
    else:
        focus_form = FocusForm()
        focus_form.fields["skill_name"].choices = [("", "— No focus skill —")] + [(n, n) for n in session_skill_names]
        formset = EvaluationFormSet(initial=initial_rows)

    today_date, now_dt = get_today_and_now()
    status_label, status_css = get_status_label_and_css(now_dt, training_class)
    enrolled_count = enrolled.values("player").distinct().count()
    stats = class_eval_stats(training_class)

    context = {
        "class_info": {
            "id": training_class.id,
            "title": training_class.session.title,
            "date_label": training_class.date.strftime("%b %d, %Y"),
            "time_label": format_time_range(training_class),
            "status_label": status_label,
            "status_css": status_css,
            "enrolled": enrolled_count,
            "coverage_pct": stats["coverage_pct"],
        },
        "focus_form": focus_form,
        "formset": formset,
        "row_names": [(row["player_id"], name_by_player[row["player_id"]]) for row in initial_rows],
        "player_skills": {pid: [s.skill.name for s in skills] for pid, skills in player_skill_map.items()},
    }

    return render(request, "trainers/take_evaluations.html", context)

