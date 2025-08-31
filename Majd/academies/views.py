from .models import Academy
from django.views.generic import DetailView, TemplateView
from django.shortcuts import render
from .models import Academy, Program, Session
from parents.models import Child
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.shortcuts import render, get_object_or_404, redirect
from .forms import ProgramForm, SessionForm, AcademyForm


def academy_list_view(request):
    academies = Academy.objects.prefetch_related("programs").all()

    #  Filters 
    search = request.GET.get("search")
    sport = request.GET.get("sport")
    city = request.GET.get("city")

    if search:
        academies = academies.filter(name__icontains=search)
    if sport:
        academies = academies.filter(programs__sport_type=sport).distinct()
    if city:
        academies = academies.filter(city=city)

    #  Stats 
    total_academies = Academy.objects.count()
    total_players = Child.objects.distinct().count()
    satisfaction_rate = 95  # static for now
    sport_choices = Program.SportType.choices
    cities = Academy.objects.values_list("city", flat=True).distinct()

    context = {
        "academies": academies,
        "total_academies": total_academies,
        "total_players": total_players,
        "satisfaction_rate": satisfaction_rate,
        "sport_choices": sport_choices,
        "cities": cities,
    }
    return render(request, "academies/academy_list.html", context)


def AcademyDetailView(request, slug):
    academy = get_object_or_404(Academy, slug=slug)

    # Years of Experience
    current_year = timezone.now().year
    years_experience = max(0, current_year - academy.establishment_year)

    # Active Students
    active_students = Child.objects.filter(
        programs__academy=academy
    ).distinct().count()

    context = {
        "academy": academy,
        "programs": academy.programs.all(),
        "coaches": academy.trainers.all(),  # ✅ هنا التعديل
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

    profile = request.user.academy_admin_profile
    academy = getattr(profile, "academy", None)

    if request.method == "POST":
        form = AcademyForm(request.POST, request.FILES, instance=academy)
        if form.is_valid():
            form.save()
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




def _academy(user):
    return user.academy_admin_profile.academy

# ✅ Programs Dashboard
@login_required
def program_dashboard(request):
    academy = _academy(request.user)

    programs = Program.objects.filter(academy=academy).prefetch_related("sessions")
    sessions = Session.objects.filter(program__academy=academy)

    total_programs = programs.count()
    total_sessions = sessions.count()
    total_enrollment = Child.objects.filter(programs__academy=academy).distinct().count()

    total_capacity = sum(s.capacity for s in sessions)
    utilization = round((total_enrollment / total_capacity) * 100, 1) if total_capacity else 0

    context = {
        "academy": academy,
        "programs": programs,
        "total_programs": total_programs,
        "total_sessions": total_sessions,
        "total_enrollment": total_enrollment,
        "utilization_pct": utilization,
        "revenue": 60450,  # placeholder
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

# ✅ Program Edit
@login_required
def program_edit(request, pk):
    academy = _academy(request.user)
    program = get_object_or_404(Program, pk=pk, academy=academy)

    if request.method == "POST":
        form = ProgramForm(request.POST, request.FILES, instance=program)
        if form.is_valid():
            form.save()
            messages.success(request, "Program updated successfully.")
            return redirect("academies:programs")
    else:
        form = ProgramForm(instance=program)

    return render(request, "academies/program_form.html", {"form": form, "program": program})

# ✅ Program Delete
@login_required
def program_delete(request, pk):
    academy = _academy(request.user)
    program = get_object_or_404(Program, pk=pk, academy=academy)

    if request.method == "POST":
        program.delete()
        messages.success(request, "Program deleted successfully.")
        return redirect("academies:programs")

    return render(request, "academies/confirm_delete.html", {"object": program})

# ✅ Session Create
@login_required
def session_create(request, program_id):
    academy = _academy(request.user)
    program = get_object_or_404(Program, pk=program_id, academy=academy)

    if request.method == "POST":
        form = SessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.program = program
            session.save()
            messages.success(request, "Session created successfully.")
            return redirect("academies:programs")
    else:
        form = SessionForm()

    return render(request, "academies/session_form.html", {"form": form, "program": program})

# ✅ Session Edit
@login_required
def session_edit(request, pk):
    academy = _academy(request.user)
    session = get_object_or_404(Session, pk=pk, program__academy=academy)

    if request.method == "POST":
        form = SessionForm(request.POST, instance=session)
        if form.is_valid():
            form.save()
            messages.success(request, "Session updated successfully.")
            return redirect("academies:programs")
    else:
        form = SessionForm(instance=session)

    return render(request, "academies/session_form.html", {"form": form, "session": session})

# ✅ Session Delete
@login_required
def session_delete(request, pk):
    academy = _academy(request.user)
    session = get_object_or_404(Session, pk=pk, program__academy=academy)

    if request.method == "POST":
        session.delete()
        messages.success(request, "Session deleted successfully.")
        return redirect("academies:programs")

    return render(request, "academies/confirm_delete.html", {"object": session})
