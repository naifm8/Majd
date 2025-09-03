from django.shortcuts import render, get_object_or_404
from networkx import reverse
from .models import Academy, Program, Session
from payment.models import SubscriptionPlan
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from .forms import ProgramForm, SessionForm, AcademyForm, SubscriptionPlanForm
from accounts.models import TrainerProfile
from parents.models import Child, Enrollment
from player.models import PlayerProfile, PlayerSession
from .forms import TrainerProfileForm
from datetime import date
from django.db.models import Q
import csv
import openpyxl
from django.http import HttpResponse
from payment.models import PlanType, SubscriptionPlan, Subscription

def _academy(user):
    return user.academy_admin_profile.academy

def _is_parent_subscribed_to_academy(parent_profile, academy):
    """
    Check if a parent is subscribed to an academy.
    """
    from parents.models import ParentSubscription
    
    try:
        subscription = ParentSubscription.objects.get(
            parent=parent_profile,
            academy=academy
        )
        return subscription.is_valid
    except ParentSubscription.DoesNotExist:
        return False

def academy_list_view(request):
    academies = Academy.objects.prefetch_related(
        "programs__enrollments__child"
    ).all()

    # Filters
    search = request.GET.get("search")
    sport = request.GET.get("sport")
    city = request.GET.get("city")

    if search:
        academies = academies.filter(name__icontains=search)
    if sport:
        academies = academies.filter(programs__sport_type=sport).distinct()
    if city:
        academies = academies.filter(city=city)

    # Stats
    total_academies = Academy.objects.count()
    total_children = Child.objects.count()  # all players in system
    total_enrolled = (
        Enrollment.objects.filter(is_active=True)
        .values("child")
        .distinct()
        .count()
    )

    context = {
        "academies": academies,
        "total_academies": total_academies,
        "total_children": total_children,   # all players
        "total_enrolled": total_enrolled,   # active enrolled players
        "satisfaction_rate": 95,
        "sport_choices": Program.SportType.choices,
        "cities": Academy.objects.exclude(city="")
                    .values_list("city", flat=True)
                    .distinct(),
    }
    return render(request, "academies/academy_list.html", context)



def AcademyDetailView(request, slug):
    academy = get_object_or_404(Academy, slug=slug)

    # Years of Experience
    current_year = timezone.now().year
    years_experience = max(0, current_year - academy.establishment_year)

    # Active Students (via Enrollment instead of Child.programs)
    active_students = Enrollment.objects.filter(
        program__academy=academy,
        is_active=True
    ).values("child").distinct().count()

    context = {
        "academy": academy,
        "programs": academy.programs.all(),
        "coaches": academy.trainers.all(), 
        "active_students": active_students,
        "fake_rating": 4.8,
        "years_experience": years_experience,
    }
    return render(request, "academies/academy_detail.html", context)
 
 

@login_required
def academy_setup_view(request):
    if not hasattr(request.user, "academy_admin_profile"):
        messages.error(request, "You must be an academy admin to access this page.")
        return redirect("main:main_home_view")

    # ✅ ensure subscription exists and is successful
    from payment.models import Subscription
    has_subscription = Subscription.objects.filter(
        contact_email=request.user.email, status="successful"
    ).exists()

    if not has_subscription:
        messages.error(request, "You must subscribe before setting up your academy.")
        return redirect("payment:subscription_step")

    profile = request.user.academy_admin_profile
    academy = getattr(profile, "academy", None)

    if request.method == "POST":
        form = AcademyForm(request.POST, request.FILES, instance=academy)
        if form.is_valid():
            academy = form.save(commit=False)
            academy.owner = profile  # ensure link
            academy.save()
            messages.success(request, "Academy profile updated successfully!")
            return redirect("academies:detail", slug=academy.slug)
    else:
        form = AcademyForm(instance=academy)

    return render(request, "academies/academy_setup.html", {"form": form})



@login_required
def AcademyDashboardView(request):
    # Ensure logged in user is academy admin
    if not hasattr(request.user, "academy_admin_profile"):
        messages.error(request, "You must be an Academy Admin to access the dashboard.")
        return redirect("main:main_home_view")

    academy = request.user.academy_admin_profile.academy

    context = {
        "academy": academy,
    }
    return render(request, "academies/dashboard_overview.html", context)


# ✅ Subscription Dashboard
@login_required
def subscription_dashboard(request):
    # Ensure logged in user is academy admin
    if not hasattr(request.user, "academy_admin_profile"):
        messages.error(request, "You must be an Academy Admin to access the dashboard.")
        return redirect("main:main_home_view")

    academy = request.user.academy_admin_profile.academy
    
    # Get all available plan types
    plan_types = PlanType.objects.all().order_by('display_order')
    
    # Get academy's subscription plans (this is the main focus)
    academy_subscription_plans = SubscriptionPlan.objects.filter(academy=academy).order_by('-created_at')
    
    # Get academy's subscription history (for reference)
    subscriptions = Subscription.objects.filter(academy_name=academy.name).order_by('-created_at')
    
    # Get current active subscription
    active_subscription = subscriptions.filter(status=Subscription.Status.SUCCESSFUL).first()
    
    context = {
        "academy": academy,
        "plan_types": plan_types,
        "academy_subscription_plans": academy_subscription_plans,
        "subscriptions": subscriptions,
        "active_subscription": active_subscription,
    }
    return render(request, "academies/subscription_dashboard.html", context)


# ✅ Add Subscription Plan
@login_required
def add_subscription_plan(request):
    # Ensure logged in user is academy admin
    if not hasattr(request.user, "academy_admin_profile"):
        messages.error(request, "You must be an Academy Admin to access this page.")
        return redirect("main:main_home_view")

    academy = request.user.academy_admin_profile.academy
    
    if request.method == 'POST':
        form = SubscriptionPlanForm(request.POST, academy=academy)
        if form.is_valid():
            subscription_plan = form.save(commit=False)
            subscription_plan.academy = academy
            subscription_plan.save()
            messages.success(request, f'Subscription plan "{subscription_plan.title}" has been created successfully!')
            return redirect('academies:subscription_dashboard')
    else:
        form = SubscriptionPlanForm(academy=academy)
    
    context = {
        'form': form,
        'academy': academy,
    }
    return render(request, 'academies/add_subscription_plan.html', context)


# ✅ Edit Subscription Plan
@login_required
def edit_subscription_plan(request, plan_id):
    # Ensure logged in user is academy admin
    if not hasattr(request.user, "academy_admin_profile"):
        messages.error(request, "You must be an Academy Admin to access this page.")
        return redirect("main:main_home_view")

    academy = request.user.academy_admin_profile.academy
    subscription_plan = get_object_or_404(SubscriptionPlan, id=plan_id, academy=academy)
    
    if request.method == 'POST':
        form = SubscriptionPlanForm(request.POST, instance=subscription_plan, academy=academy)
        if form.is_valid():
            form.save()
            messages.success(request, f'Subscription plan "{subscription_plan.title}" has been updated successfully!')
            return redirect('academies:subscription_dashboard')
    else:
        form = SubscriptionPlanForm(instance=subscription_plan, academy=academy)
    
    context = {
        'form': form,
        'subscription_plan': subscription_plan,
        'academy': academy,
    }
    return render(request, 'academies/edit_subscription_plan.html', context)


# ✅ Delete Subscription Plan
@login_required
def delete_subscription_plan(request, plan_id):
    # Ensure logged in user is academy admin
    if not hasattr(request.user, "academy_admin_profile"):
        messages.error(request, "You must be an Academy Admin to access this page.")
        return redirect("main:main_home_view")

    academy = request.user.academy_admin_profile.academy
    subscription_plan = get_object_or_404(SubscriptionPlan, id=plan_id, academy=academy)
    
    if request.method == 'POST':
        plan_name = subscription_plan.plan_type.name
        subscription_plan.delete()
        messages.success(request, f'Subscription plan "{plan_name}" has been deleted successfully!')
        return redirect('academies:subscription_dashboard')
    
    context = {
        'subscription_plan': subscription_plan,
        'academy': academy,
    }
    return render(request, 'academies/delete_subscription_plan.html', context)


# ✅ Subscription Enrollment Redirect
def subscription_enroll_redirect(request, academy_slug, plan_id):
    """
    Redirect users based on their authentication status and profile type:
    - If authenticated parent: redirect to parent dashboard
    - If not authenticated: redirect to get started page
    """
    if request.user.is_authenticated:
        # Check if user has a parent profile
        if hasattr(request.user, 'parent_profile'):
            # Redirect to parent subscriptions page
            return redirect('parents:subscriptions')
        else:
            # User is authenticated but not a parent, redirect to get started
            return redirect('accounts:selection_view')
    else:
        # Not authenticated, redirect to get started
        return redirect('accounts:selection_view')


# ✅ Programs Dashboard
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render

from academies.models import Program, Session
from parents.models import Enrollment  # <-- use Enrollment to count players

def _academy(user):
    return user.academy_admin_profile.academy

@login_required
def program_dashboard(request):
    # Which programs to show
    if request.user.is_superuser:
        programs = Program.objects.all().prefetch_related("sessions")
        academy = None
    else:
        academy = _academy(request.user)
        programs = (
            Program.objects
            .filter(academy=academy)
            .prefetch_related("sessions")
        )

    # Sessions under those programs
    sessions = (
        Session.objects
        .filter(program__in=programs)
        .select_related("program")
    )

    # Stats
    total_programs = programs.count()
    total_sessions = sessions.count()

    # ✅ Use Enrollment instead of Child.programs
    total_enrollment = (
        Enrollment.objects
        .filter(program__in=programs, is_active=True)
        .values("child")
        .distinct()
        .count()
    )

    total_capacity = sessions.aggregate(total=Sum("capacity"))["total"] or 0
    utilization = round((total_enrollment / total_capacity) * 100, 1) if total_capacity else 0

    context = {
        "academy": academy,
        "programs": programs,
        "total_programs": total_programs,
        "total_sessions": total_sessions,
        "total_enrollment": total_enrollment,
        "utilization_pct": utilization,
        "revenue": 60450,  # placeholder
        "total_capacity": total_capacity,  # if your template uses it
    }
    return render(request, "academies/dashboard_programs.html", context)




# ✅ Program Create
@login_required
def program_create(request):
    academy = _academy(request.user)

    if request.method == "POST":
        form = ProgramForm(request.POST, request.FILES)
        if form.is_valid():
            program = form.save(commit=False)
            program.academy = academy
            program.save()
            messages.success(request, "Program created successfully.")
            return redirect("academies:programs")
    else:
        form = ProgramForm()

    return render(request, "academies/program_form.html", {"form": form})


@login_required
def program_edit(request, pk):
    program = get_object_or_404(Program, pk=pk)

    if request.method == "POST":
        form = ProgramForm(request.POST, request.FILES, instance=program)
        if form.is_valid():
            form.save()
            messages.success(request, "Program updated successfully!")
            return redirect("academies:programs")
    else:
        form = ProgramForm(instance=program)

    return render(request, "academies/program_form.html", {"form": form, "program": program})


@login_required
def program_delete(request, pk):
    program = get_object_or_404(Program, pk=pk)

    if request.method == "POST":
        program.delete()
        messages.success(request, "Program deleted successfully!")
        return redirect("academies:programs")

    return render(request, "academies/program_confirm_delete.html", {"program": program})



@login_required
def session_create(request, program_id):
    academy = _academy(request.user)
    program = get_object_or_404(Program, id=program_id, academy=academy)

    if request.method == "POST":
        form = SessionForm(request.POST, academy=academy)  # ✅ pass academy
        if form.is_valid():
            session = form.save(commit=False)
            session.program = program
            session.save()
            messages.success(request, "Session created successfully ✅")
            return redirect("academies:programs")
    else:
        form = SessionForm(academy=academy)  # ✅ pass academy

    return render(request, "academies/session_form.html", {
        "form": form,
        "program": program,
    })




@login_required
def session_edit(request, pk):
    academy = _academy(request.user)
    session = get_object_or_404(Session, pk=pk, program__academy=academy)

    if request.method == "POST":
        form = SessionForm(request.POST, academy=academy, instance=session)
        if form.is_valid():
            form.save()
            messages.success(request, "Session updated successfully ✅")
            return redirect("academies:programs")
    else:
        form = SessionForm(academy=academy, instance=session)

    return render(request, "academies/session_form.html", {
        "form": form,
        "program": session.program,
        "is_edit": True,  # 👈 helps toggle template title/button
    })


@login_required
def session_delete(request, pk):
    academy = _academy(request.user)
    session = get_object_or_404(Session, pk=pk, program__academy=academy)

    if request.method == "POST":
        session.delete()
        messages.success(request, "Session deleted successfully 🗑️")
        return redirect("academies:programs")

    return render(request, "academies/session_confirm_delete.html", {
        "session": session,
    })


@login_required
def program_sessions(request, academy_slug, program_id):
    academy = get_object_or_404(Academy, slug=academy_slug)
    program = get_object_or_404(Program, id=program_id, academy=academy)

    # Base query
    sessions = (
        Session.objects.filter(program=program)
        .select_related("trainer")
        .prefetch_related("slots")
    )

    # Collect distinct dynamic age ranges
    age_ranges = (
        sessions.values_list("age_min", "age_max")
        .distinct()
        .order_by("age_min")
    )

    # --- Filters ---
    level = request.GET.get("level")
    gender = request.GET.get("gender")
    age = request.GET.get("age")  # e.g. "6-10"

    if level and level != "all":
        sessions = sessions.filter(level=level)

    if gender and gender != "all":
        sessions = sessions.filter(gender=gender)

    if age and age != "all":
        try:
            age_min, age_max = map(int, age.replace(" ", "").split("-"))
            sessions = sessions.filter(age_min__lte=age_min, age_max__gte=age_max)
        except ValueError:
            pass

    context = {
        "academy": academy,
        "program": program,
        "sessions": sessions,
        "filters": {
            "level": level or "all",
            "gender": gender or "all",
            "age": age or "all",
        },
        "age_ranges": age_ranges,  # 👈 send to template
    }
    return render(request, "academies/sessions_page.html", context)





@login_required
def trainer_dashboard(request):
    academy_admin = getattr(request.user, "academy_admin_profile", None)

    # ✅ Protect against missing academy
    academy = academy_admin.academy if academy_admin and academy_admin.academy else None

    if not academy:
        messages.error(request, "No Academy assigned to your account.")
        return redirect("academies:dashboard")  # fallback or main dashboard

    trainers = TrainerProfile.objects.filter(academy=academy).prefetch_related("sessions", "sessions__program")

    total_trainers = trainers.count()
    total_players = PlayerProfile.objects.filter(academy=academy).count()
    total_sessions = Session.objects.filter(program__academy=academy).count()

    trainer_data = []
    for trainer in trainers:
        player_count = PlayerProfile.objects.filter(academy=trainer.academy).distinct().count()

        session_data = []
        for session in trainer.sessions.all():
            enrolled = PlayerProfile.objects.filter(academy=session.program.academy).count()
            session_data.append((session, enrolled))

        trainer_data.append((trainer, player_count, session_data))

    context = {
        "academy": academy,
        "trainer_data": trainer_data,
        "total_trainers": total_trainers,
        "total_players": total_players,
        "total_sessions": total_sessions,
    }
    return render(request, "academies/trainer_dashboard.html", context)


@login_required
def add_trainer(request):
    # Ensure only academy admins can add trainers
    academy_admin = getattr(request.user, "academy_admin_profile", None)
    if not academy_admin:
        messages.error(request, "You must be an Academy Admin to add trainers.")
        return redirect("main:main_home_view")

    academy = academy_admin.academy

    if request.method == "POST":
        form = TrainerProfileForm(request.POST, request.FILES)
        if form.is_valid():
            trainer = form.save(commit=False)
            trainer.academy = academy
            trainer.save()
            messages.success(request, f"Trainer {trainer.user.get_full_name()} added successfully!")
            return redirect("academies:trainer_dashboard")
    else:
        form = TrainerProfileForm()

    return render(request, "academies/add_trainer.html", {"form": form, "academy": academy})

def calculate_age(born):
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


@login_required
def players_dashboard(request):
    academy_admin = getattr(request.user, "academy_admin_profile", None)
    academy = academy_admin.academy if academy_admin else None

    players = PlayerProfile.objects.filter(academy=academy) if academy else PlayerProfile.objects.all()

    # 🔍 Search
    query = request.GET.get("q")
    if query:
        players = players.filter(
            Q(child__first_name__icontains=query) |
            Q(child__last_name__icontains=query) |
            Q(position__name__icontains=query)
        )

    # 🔽 Filter by injury risk
    injury_filter = request.GET.get("injury")
    if injury_filter:
        if injury_filter == "low":
            players = players.filter(avg_progress__gte=70)
        elif injury_filter == "medium":
            players = players.filter(avg_progress__lt=70, avg_progress__gte=40)
        elif injury_filter == "high":
            players = players.filter(avg_progress__lt=40)

    players = players.prefetch_related("player_sessions__session")

    # --- Export CSV / Excel ---
    export_type = request.GET.get("export")
    if export_type in ["csv", "excel"]:
        return export_players(players, export_type)

    # Stats
    total_players = players.count()
    active_players = players.filter(avg_progress__gte=50).count()
    injured_players = players.filter(class_attendances__status="excused").distinct().count()

    player_data = []
    for player in players:
        session = player.player_sessions.first().session if player.player_sessions.exists() else None
        status = "On Schedule" if session else "Not Enrolled"

        # Injury risk rule
        if player.avg_progress < 40:
            risk = "High"
        elif player.avg_progress < 70:
            risk = "Medium"
        else:
            risk = "Low"

        player_data.append((player, session, status, risk))

    context = {
        "academy": academy,
        "total_players": total_players,
        "active_players": active_players,
        "injured_players": injured_players,
        "player_data": player_data,
        "query": query or "",
        "injury_filter": injury_filter or "",
    }
    return render(request, "academies/players_dashboard.html", context)


def export_players(players, export_type):
    if export_type == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="players.csv"'

        writer = csv.writer(response)
        writer.writerow(["Name", "Session", "Level", "Status", "Injury Risk"])

        for player in players:
            session = player.player_sessions.first().session if player.player_sessions.exists() else None
            session_title = session.title if session else "N/A"
            level = session.get_level_display() if session else "N/A"
            status = "On Schedule" if session else "Not Enrolled"

            # Injury risk
            if player.avg_progress < 40:
                risk = "High"
            elif player.avg_progress < 70:
                risk = "Medium"
            else:
                risk = "Low"

            writer.writerow([f"{player.child.first_name} {player.child.last_name}", session_title, level, status, risk])

        return response

    elif export_type == "excel":
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "Players"

        headers = ["Name", "Session", "Level", "Status", "Injury Risk"]
        sheet.append(headers)

        for player in players:
            session = player.player_sessions.first().session if player.player_sessions.exists() else None
            session_title = session.title if session else "N/A"
            level = session.get_level_display() if session else "N/A"
            status = "On Schedule" if session else "Not Enrolled"

            if player.avg_progress < 40:
                risk = "High"
            elif player.avg_progress < 70:
                risk = "Medium"
            else:
                risk = "Low"

            sheet.append([f"{player.child.first_name} {player.child.last_name}", session_title, level, status, risk])

        response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = 'attachment; filename="players.xlsx"'
        workbook.save(response)
        return response


@login_required
def join_program_view(request, academy_slug, program_id):
    # step 1
    academy = get_object_or_404(Academy, slug=academy_slug)
    program = get_object_or_404(Program, id=program_id, academy=academy)

    parent_profile = getattr(request.user, "parent_profile", None)
    if not parent_profile:
        messages.error(request, "Only parents can join programs.")
        return redirect("academies:detail", slug=academy.slug)

    children = Child.objects.filter(parent=parent_profile)

    # derive min/max from sessions
    sessions = program.sessions.all()
    if sessions.exists():
        min_age = min(s.age_min for s in sessions)
        max_age = max(s.age_max for s in sessions)
    else:
        min_age = None
        max_age = None
        
    # annotate children with eligibility
    for child in children:
        child.age = calculate_age(child.date_of_birth) if child.date_of_birth else None
        if min_age is not None and max_age is not None and child.age is not None:
            child.is_eligible = min_age <= child.age <= max_age
        else:
            child.is_eligible = True  # if no age restriction
        child.already_enrolled = Enrollment.objects.filter(child=child, program=program).exists()

    if request.method == "POST":
        selected_ids = request.POST.getlist("children")
        if not selected_ids:
            messages.warning(request, "Please select at least one child.")
            return redirect("academies:join_program_view", academy_slug=academy.slug, program_id=program.id)

        # Store selected children temporarily (session)
        request.session["selected_children"] = selected_ids
        
        # Go to Step 2 (select sessions)
        return redirect("academies:enrollment_sessions", academy_slug=academy.slug, program_id=program.id)


    return render(request, "academies/join_program.html", {
        "academy": academy,
        "program": program,
        "children": children,
        "min_age": min_age,
        "max_age": max_age,
    })


@login_required
def enrollment_sessions_view(request, academy_slug, program_id):
    # step 2: choose sessions
    academy = get_object_or_404(Academy, slug=academy_slug)
    program = get_object_or_404(Program, id=program_id, academy=academy)

    parent_profile = getattr(request.user, "parent_profile", None)
    if not parent_profile:
        messages.error(request, "Only parents can join programs.")
        return redirect("academies:detail", slug=academy.slug)

    # All sessions for this program
    sessions = (
        Session.objects.filter(program=program)
        .select_related("trainer")
        .prefetch_related("slots", "required_skills")
    )

    # Distinct age ranges for filters
    age_ranges = (
        sessions.values_list("age_min", "age_max")
        .distinct()
        .order_by("age_min")
    )

    # --- Filters ---
    level = request.GET.get("level")
    gender = request.GET.get("gender")
    age = request.GET.get("age")  # e.g. "6-10"

    if level and level != "all":
        sessions = sessions.filter(level=level)

    if gender and gender != "all":
        sessions = sessions.filter(gender=gender)

    if age and age != "all":
        try:
            age_min, age_max = map(int, age.replace(" ", "").split("-"))
            sessions = sessions.filter(age_min__lte=age_min, age_max__gte=age_max)
        except ValueError:
            pass

    # Handle POST (user selecting sessions)
    if request.method == "POST":
        selected_sessions = request.POST.getlist("sessions")

        if not selected_sessions:
            messages.error(request, "You did not select any session.", "alert-danger")
        else:
            # store as integers in session
            request.session["selected_sessions"] = [int(sid) for sid in selected_sessions]
            messages.success(request, "Sessions selected successfully!")

            # Go to Step 3 (enrollment details)
            return redirect(
                "academies:enrollment_details",
                academy_slug=academy.slug,
                program_id=program.id,
            )

    context = {
        "academy": academy,
        "program": program,
        "sessions": sessions,
        "filters": {
            "level": level or "all",
            "gender": gender or "all",
            "age": age or "all",
        },
        "age_ranges": age_ranges,
    }
    return render(request, "academies/enrollment_sessions.html", context)


@login_required
def enrollment_details_view(request, academy_slug, program_id):
    academy = get_object_or_404(Academy, slug=academy_slug)
    program = get_object_or_404(Program, id=program_id, academy=academy)

    parent_profile = getattr(request.user, "parent_profile", None)
    if not parent_profile:
        messages.error(request, "Only parents can join programs.")
        return redirect("academies:detail", slug=academy.slug)

    # cast child IDs to int
    selected_child_ids = [int(cid) for cid in request.session.get("selected_children", [])]
    children = Child.objects.filter(id__in=selected_child_ids, parent=parent_profile)

    # cast session IDs to int
    selected_session_ids = [int(sid) for sid in request.session.get("selected_sessions", [])]
    sessions = Session.objects.filter(id__in=selected_session_ids, program=program)

    if not children.exists():
        messages.error(request, "No children selected for enrollment.")
        return redirect("academies:join_program_view", academy_slug=academy.slug, program_id=program.id)

    if not sessions.exists():
        messages.error(request, "No sessions selected for enrollment.")
        return redirect("academies:enrollment_sessions", academy_slug=academy.slug, program_id=program.id)

    if request.method == "POST":
        emergency_name = request.POST.get("emergency_name", "").strip()
        emergency_phone = request.POST.get("emergency_phone", "").strip()

        if not emergency_name or not emergency_phone:
            messages.error(request, "Emergency contact name and phone are required.")
            return redirect("academies:enrollment_details", academy_slug=academy.slug, program_id=program.id)

        # Check if parent is subscribed to this academy
        is_subscribed = _is_parent_subscribed_to_academy(parent_profile, academy)
        
        if not is_subscribed:
            messages.warning(request, f"You need to subscribe to {academy.name} before enrolling your children.")
            # Redirect to payments page with academy info
            from django.urls import reverse
            payments_url = reverse('parents:payments') + f'?academy={academy.slug}'
            return redirect(payments_url)

        for child in children:
            enrollment, created = Enrollment.objects.get_or_create(
                child=child,
                program=program,
                defaults={
                    "emergency_contact_name": emergency_name,
                    "emergency_contact_phone": emergency_phone,
                },
            )

            # Attach sessions
            enrollment.sessions.set(sessions)

            # Create PlayerSession
            if hasattr(child, "player_profile"):
                player = child.player_profile

                # Update academy if not already set or different
                if player.academy != academy:
                    player.academy = academy
                    player.save()

                for session in sessions:
                    PlayerSession.objects.get_or_create(
                        player=child.player_profile,
                        session=session,
                    )

        request.session.pop("selected_children", None)
        request.session.pop("selected_sessions", None)

        messages.success(request, f"Enrollment completed for {len(children)} child(ren).")
        return redirect("parents:dashboard")

    return render(request, "academies/enrollment_details.html", {
        "academy": academy,
        "program": program,
        "children": children,
        "sessions": sessions,
    })



