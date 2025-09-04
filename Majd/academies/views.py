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
from .forms import ProgramForm, SessionForm, AcademyForm
from accounts.models import TrainerProfile, AcademyAdminProfile
from parents.models import Child, Enrollment
from player.models import PlayerProfile, PlayerSession
from .forms import TrainerProfileForm
from datetime import date
from django.db.models import Q
import csv
import openpyxl
from django.http import HttpResponse, HttpRequest
from payment.models import PlanType, SubscriptionPlan, Subscription
from django.db.models import Sum

def _academy(user):
    return user.academy_admin_profile.academy


def _is_parent_subscribed_to_academy(parent_profile, academy):
    """
    Check if a parent has an active, valid subscription to the academy.
    """
    from parents.models import ParentSubscription

    today = timezone.now().date()
    try:
        subscription = ParentSubscription.objects.get(
            parent=parent_profile,
            academy=academy,
        )

        if hasattr(subscription, "start_date") and hasattr(subscription, "end_date"):
            return subscription.start_date <= today <= subscription.end_date

        return getattr(subscription, "is_active", True)
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


    total_academies = Academy.objects.count()
    total_children = Child.objects.count() 
    total_enrolled = (
        Enrollment.objects.filter(is_active=True)
        .values("child")
        .distinct()
        .count()
    )

    context = {
        "academies": academies,
        "total_academies": total_academies,
        "total_children": total_children,  
        "total_enrolled": total_enrolled, 
        "satisfaction_rate": 95,
        "sport_choices": Program.SportType.choices,
        "cities": Academy.objects.exclude(city="")
                    .values_list("city", flat=True)
                    .distinct(),
    }
    return render(request, "academies/academy_list.html", context)



def AcademyDetailView(request, slug):
    academy = get_object_or_404(Academy, slug=slug)


    current_year = timezone.now().year
    years_experience = max(0, current_year - academy.establishment_year)


    active_students = Enrollment.objects.filter(
        program__academy=academy,
        is_active=True
    ).values("child").distinct().count()


    from payment.models import SubscriptionPlan
    subscription_plans = SubscriptionPlan.objects.filter(
        academy=academy,
        is_active=True
    ).order_by('price')
    

    is_subscribed = False
    if request.user.is_authenticated and hasattr(request.user, 'parent_profile'):
        from parents.models import ParentSubscription

        valid_subscriptions = ParentSubscription.objects.filter(
            parent=request.user.parent_profile,
            academy=academy,
            is_active=True
        )

        is_subscribed = any(sub.is_valid for sub in valid_subscriptions)
    
    context = {
        "academy": academy,
        "programs": academy.programs.all(),
        "coaches": academy.trainers.all(), 
        "active_students": active_students,
        "fake_rating": 4.8,
        "years_experience": years_experience,
        "is_subscribed": is_subscribed,
        "subscription_plans": subscription_plans,
    }
    return render(request, "academies/academy_detail.html", context)
 
 

@login_required
def academy_setup_view(request):
    if not hasattr(request.user, "academy_admin_profile"):
        messages.error(request, "You must be an academy admin to access this page.")
        return redirect("main:main_home_view")

    # from payment.models import Subscription
    # has_subscription = Subscription.objects.filter(
    #     contact_email=request.user.email, status="successful"
    # ).exists()

    # if not has_subscription:
    #     messages.error(request, "You must subscribe before setting up your academy.")
    #     return redirect("payment:subscription_step")

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

    if not hasattr(request.user, "academy_admin_profile"):
        messages.error(request, "You must be an Academy Admin to access the dashboard.")
        return redirect("main:main_home_view")

    academy = request.user.academy_admin_profile.academy

    context = {
        "academy": academy,
    }
    return render(request, "academies/dashboard_overview.html", context)



@login_required
def subscription_dashboard(request):

    if not hasattr(request.user, "academy_admin_profile"):
        messages.error(request, "You must be an Academy Admin to access the dashboard.")
        return redirect("main:main_home_view")

    academy = request.user.academy_admin_profile.academy
    

    plan_types = PlanType.objects.all().order_by('display_order')
    

    academy_subscription_plans = SubscriptionPlan.objects.filter(academy=academy).order_by('-created_at')
    

    subscriptions = Subscription.objects.filter(academy_name=academy.name).order_by('-created_at')
    

    active_subscription = subscriptions.filter(status=Subscription.Status.SUCCESSFUL).first()
    
    context = {
        "academy": academy,
        "plan_types": plan_types,
        "academy_subscription_plans": academy_subscription_plans,
        "subscriptions": subscriptions,
        "active_subscription": active_subscription,
    }
    return render(request, "academies/subscription_dashboard.html", context)



@login_required
def add_subscription_plan(request):

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



@login_required
def edit_subscription_plan(request, plan_id):
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



@login_required
def delete_subscription_plan(request, plan_id):
    if not hasattr(request.user, "academy_admin_profile"):
        messages.error(request, "You must be an Academy Admin to access this page.")
        return redirect("main:main_home_view")

    academy = request.user.academy_admin_profile.academy
    subscription_plan = get_object_or_404(SubscriptionPlan, id=plan_id, academy=academy)
    
    if request.method == 'POST':
        plan_name = subscription_plan.plan_type.name if subscription_plan.plan_type else subscription_plan.title
        subscription_plan.delete()
        messages.success(request, f'Subscription plan "{plan_name}" has been deleted successfully!')
        return redirect('academies:subscription_dashboard')
    
    context = {
        'subscription_plan': subscription_plan,
        'academy': academy,
    }
    return render(request, 'academies/delete_subscription_plan.html', context)



def subscription_enroll_redirect(request, academy_slug, plan_id):
    """
    Redirect users based on their authentication status and profile type:
    - If authenticated parent: redirect to parent dashboard
    - If not authenticated: redirect to get started page
    """
    if request.user.is_authenticated:
        # Check if user has a parent profile
        if hasattr(request.user, 'parent_profile'):
            return redirect('parents:subscriptions')
        else:
            return redirect('accounts:selection_view')
    else:
        return redirect('accounts:selection_view')


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
        "revenue": 60450, 
        "total_capacity": total_capacity, 
    }
    return render(request, "academies/dashboard_programs.html", context)




#  Program Create
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
        form = SessionForm(request.POST, academy=academy)  
        if form.is_valid():
            session = form.save(commit=False)
            session.program = program
            session.save()
            messages.success(request, "Session created successfully ")
            return redirect("academies:programs")
    else:
        form = SessionForm(academy=academy) 

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
            messages.success(request, "Session updated successfully ")
            return redirect("academies:programs")
    else:
        form = SessionForm(academy=academy, instance=session)

    return render(request, "academies/session_form.html", {
        "form": form,
        "program": session.program,
        "is_edit": True, 
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


    age_ranges = (
        sessions.values_list("age_min", "age_max")
        .distinct()
        .order_by("age_min")
    )


    level = request.GET.get("level")
    gender = request.GET.get("gender")
    age = request.GET.get("age") 

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
        "age_ranges": age_ranges, 
    }
    return render(request, "academies/sessions_page.html", context)





@login_required
def trainer_dashboard(request):
    academy_admin = getattr(request.user, "academy_admin_profile", None)
    academy = academy_admin.academy if academy_admin and academy_admin.academy else None
    if not academy:
        messages.error(request, "No Academy assigned to your account.")
        return redirect("academies:dashboard")

    
    trainers_all = TrainerProfile.objects.filter(academy=academy)
    trainers = trainers_all.filter(
        approval_status=TrainerProfile.ApprovalStatus.APPROVED
    ).prefetch_related("sessions", "sessions__program")

    total_trainers = trainers.count()
    total_players = PlayerProfile.objects.filter(academy=academy).count()
    total_sessions = Session.objects.filter(program__academy=academy).count()

    pending_recruitments = trainers_all.filter(
        approval_status=TrainerProfile.ApprovalStatus.PENDING
    ).count()

    trainer_data = []
    for trainer in trainers:
        player_count = (
            PlayerProfile.objects
            .filter(player_sessions__session__trainer=trainer)
            .distinct()
            .count()
        )

        session_data = []
        for session in trainer.sessions.all():
            enrolled = (
                PlayerSession.objects
                .filter(session=session)
                .values("player")
                .distinct()
                .count()
            )
            session_data.append((session, enrolled))

        trainer_data.append((trainer, player_count, session_data))

    context = {
        "academy": academy,
        "trainer_data": trainer_data,
        "total_trainers": total_trainers,
        "total_players": total_players,
        "total_sessions": total_sessions,
        "pending_recruitments": pending_recruitments,
    }
    return render(request, "academies/trainer_dashboard.html", context)


@login_required
def add_trainer(request):

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
def academy_pending_trainers_view(request: HttpRequest):
    academy_admin = getattr(request.user, "academy_admin_profile", None)
    if not academy_admin:
        messages.error(request, "You must be an Academy Admin to review trainer applications.")
        return redirect("main:main_home_view")

    academy = getattr(academy_admin, "academy", None)
    if academy is None:
        messages.error(request, "Your admin profile is not linked to any academy.")
        return redirect("main:main_home_view")

    if request.method == "POST":
        trainer_id = request.POST.get("trainer_id")
        action = request.POST.get("action")

        trainer = get_object_or_404(TrainerProfile, id=trainer_id)

        if trainer.academy_id != academy.id:
            messages.error(request, "You cannot modify a trainer outside your academy.")
            return redirect("trainers:academy_pending_trainers_view")

        if action == "approve":
            trainer.approval_status = TrainerProfile.ApprovalStatus.APPROVED
            trainer.save()
            messages.success(request, f"Approved: {trainer}")
        elif action == "reject":
            trainer.approval_status = TrainerProfile.ApprovalStatus.REJECTED

            # trainer.academy = None
            trainer.save()
            messages.info(request, f"Rejected: {trainer}")
        else:
            messages.error(request, "Unknown action.")

        return redirect("academies:academy_pending_trainers_view")


    pending_trainers = (
        TrainerProfile.objects
        .filter(academy_id=academy.id, approval_status=TrainerProfile.ApprovalStatus.PENDING)
        .select_related("user", "academy")
    )

    context = {
        "academy": academy,
        "pending_trainers": pending_trainers,
    }
    return render(request, "academies/test_add_trainers.html", context)




@login_required
def players_dashboard(request):
    academy_admin = getattr(request.user, "academy_admin_profile", None)
    academy = academy_admin.academy if academy_admin else None

    players = PlayerProfile.objects.filter(academy=academy) if academy else PlayerProfile.objects.all()


    query = request.GET.get("q")
    if query:
        players = players.filter(
            Q(child__first_name__icontains=query) |
            Q(child__last_name__icontains=query) |
            Q(position__name__icontains=query)
        )


    injury_filter = request.GET.get("injury")
    if injury_filter:
        if injury_filter == "low":
            players = players.filter(avg_progress__gte=70)
        elif injury_filter == "medium":
            players = players.filter(avg_progress__lt=70, avg_progress__gte=40)
        elif injury_filter == "high":
            players = players.filter(avg_progress__lt=40)

    players = players.prefetch_related("player_sessions__session")


    export_type = request.GET.get("export")
    if export_type in ["csv", "excel"]:
        return export_players(players, export_type)


    total_players = players.count()
    active_players = players.filter(avg_progress__gte=50).count()
    injured_players = players.filter(class_attendances__status="excused").distinct().count()

    player_data = []
    for player in players:
        session = player.player_sessions.first().session if player.player_sessions.exists() else None
        status = "On Schedule" if session else "Not Enrolled"


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
    academy = get_object_or_404(Academy, slug=academy_slug)
    program = get_object_or_404(Program, id=program_id, academy=academy)

    parent_profile = getattr(request.user, "parent_profile", None)
    if not parent_profile:
        messages.error(request, "Only parents can join programs.")
        return redirect("academies:detail", slug=academy.slug)

    children = Child.objects.filter(parent=parent_profile)


    sessions = program.sessions.all()
    if sessions.exists():
        min_age = min(s.age_min for s in sessions)
        max_age = max(s.age_max for s in sessions)
    else:
        min_age = None
        max_age = None


    for child in children:
        child.age = calculate_age(child.date_of_birth) if child.date_of_birth else None


        if min_age is not None and max_age is not None and child.age is not None:
            child.is_eligible = min_age <= child.age <= max_age
        else:
            child.is_eligible = True


        existing_enrollments = (
            Enrollment.objects.filter(child=child, is_active = True)
            .select_related("program__academy")
        )


        if existing_enrollments.filter(program=program).exists():
            child.already_enrolled = True
            child.enrolled_academy = academy
            child.enrolled_program = program


        elif existing_enrollments.exclude(program__academy=academy).exists():
            child.already_enrolled = True
            active_enrollment = existing_enrollments.exclude(program__academy=academy).first()
            child.enrolled_academy = active_enrollment.program.academy if active_enrollment else None
            child.enrolled_program = None

        else:
            child.already_enrolled = False
            child.enrolled_academy = None
            child.enrolled_program = None

    if request.method == "POST":
        selected_ids = request.POST.getlist("children")
        if not selected_ids:
            messages.warning(request, "Please select at least one child.")
            return redirect("academies:join_program_view", academy_slug=academy.slug, program_id=program.id)

        for child_id in selected_ids:
            child = get_object_or_404(Child, id=child_id, parent=parent_profile)
            existing_enrollments = Enrollment.objects.filter(child=child, is_active = True).select_related("program__academy")


            if existing_enrollments.filter(program=program).exists():
                messages.error(request, f"{child.first_name} is already enrolled in {program.title}.")
                return redirect("academies:join_program_view", academy_slug=academy.slug, program_id=program.id)


            if existing_enrollments.exclude(program__academy=academy).exists():
                other_academy = existing_enrollments.first().program.academy
                messages.error(request, f"{child.first_name} is already enrolled in {other_academy.name}.")
                return redirect("academies:join_program_view", academy_slug=academy.slug, program_id=program.id)


        request.session["selected_children"] = selected_ids
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

    academy = get_object_or_404(Academy, slug=academy_slug)
    program = get_object_or_404(Program, id=program_id, academy=academy)

    parent_profile = getattr(request.user, "parent_profile", None)
    if not parent_profile:
        messages.error(request, "Only parents can join programs.")
        return redirect("academies:detail", slug=academy.slug)


    selected_child_ids = [int(cid) for cid in request.session.get("selected_children", [])]
    children = Child.objects.filter(id__in=selected_child_ids, parent=parent_profile)


    sessions = (
        Session.objects.filter(program=program)
        .select_related("trainer")
        .prefetch_related("slots", "required_skills")
    )


    age_ranges = (
        sessions.values_list("age_min", "age_max")
        .distinct()
        .order_by("age_min")
    )


    level = request.GET.get("level")
    gender = request.GET.get("gender")
    age = request.GET.get("age")

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




    if request.method == "POST":
        selected_sessions = request.POST.getlist("sessions")

        if not selected_sessions:
            messages.error(request, "You did not select any session.", "alert-danger")
        else:
            request.session["selected_sessions"] = [int(sid) for sid in selected_sessions]
            

            return redirect(
                "academies:enrollment_details",
                academy_slug=academy.slug,
                program_id=program.id,
            )

    context = {
        "academy": academy,
        "program": program,
        "sessions": sessions,
        "children": children,
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

    selected_child_ids = [int(cid) for cid in request.session.get("selected_children", [])]
    children = Child.objects.filter(id__in=selected_child_ids, parent=parent_profile)

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

        

        for child in children:

            existing_sessions = Session.objects.filter(
                enrollments__child=child,
                enrollments__is_active=True
            ).prefetch_related("slots")

            for new_session in sessions.prefetch_related("slots"):
                for existing in existing_sessions:

                    if not (
                        new_session.end_datetime.date() < existing.start_datetime.date()
                        or new_session.start_datetime.date() > existing.end_datetime.date()
                    ):

                        for new_slot in new_session.slots.all():
                            for exist_slot in existing.slots.all():
                                if new_slot.weekday == exist_slot.weekday:
                                    if not (
                                        new_slot.end_time <= exist_slot.start_time
                                        or new_slot.start_time >= exist_slot.end_time
                                    ):
                                        messages.error(
                                            request,
                                            f"{child.first_name} already has a session ({existing.title}) "
                                            f"that overlaps with {new_session.title} on {new_slot.get_weekday_display()}.",
                                            extra_tags='alert-danger'
                                        )
                                        return redirect("academies:enrollment_sessions",
                                                        academy_slug=academy.slug,
                                                        program_id=program.id)


            enrollment, created = Enrollment.objects.get_or_create(
                child=child,
                program=program,
                defaults={
                    "emergency_contact_name": emergency_name,
                    "emergency_contact_phone": emergency_phone,
                    "is_active": True,
                },
            )
            if not created:
                enrollment.emergency_contact_name = emergency_name
                enrollment.emergency_contact_phone = emergency_phone
                enrollment.is_active = True
                enrollment.save()

            for session in sessions:
                enrollment.sessions.add(session)

            # Link to PlayerProfile
            if hasattr(child, "player_profile"):
                player = child.player_profile
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

        messages.success(request, f"Enrollment completed for {len(children)} child(ren).", extra_tags='alert-success')
        return redirect("academies:detail", slug=academy.slug)

    return render(request, "academies/enrollment_details.html", {
        "academy": academy,
        "program": program,
        "children": children,
        "sessions": sessions,
    })



