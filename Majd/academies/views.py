from django.views.generic import DetailView, TemplateView
from django.shortcuts import render, get_object_or_404
from .models import Academy, Program, Session
from parents.models import Child, Enrollment
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




@login_required
def join_academy_view(request, slug):
    academy = get_object_or_404(Academy, slug=slug)

    parent_profile = getattr(request.user, "parent_profile", None)
    if not parent_profile:
        messages.error(request, "Only parents can join academies.")
        return redirect("academies:detail", slug=academy.slug)

    children = Child.objects.filter(parent=parent_profile)
    programs = academy.programs.all()  # all programs in this academy

    if request.method == "POST":
        selected_ids = request.POST.getlist("children")
        program_id = request.POST.get("program")

        if not selected_ids or not program_id:
            messages.warning(request, "Please select children and a program.")
            return redirect("academies:join_academy_view", slug=academy.slug)

        program = get_object_or_404(Program, id=program_id, academy=academy)

        for child_id in selected_ids:
            child = get_object_or_404(Child, id=child_id, parent=parent_profile)

            Enrollment.objects.get_or_create(child=child, program=program)

            print(f"Enroll {child.first_name} in {program.title} ({academy.name})")

        messages.success(request, "Your children have been enrolled successfully!")
        return redirect("academies:academy_detail", slug=academy.slug)

    return render(request, "academies/join_academy.html", {
        "academy": academy,
        "children": children,
        "programs": programs,
    })

# ✅ Programs Dashboard
@login_required
def program_dashboard(request):
    if request.user.is_superuser:
        programs = Program.objects.all().prefetch_related("sessions")
        academy = None
    else:
        academy = _academy(request.user)
        programs = Program.objects.filter(academy=academy).prefetch_related("sessions")

    sessions = Session.objects.filter(program__in=programs)

    # Global stats
    total_programs = programs.count()
    total_sessions = sessions.count()
    total_enrollment = Child.objects.filter(programs__in=programs).distinct().count()

    total_capacity = sum(s.capacity for s in sessions)
    utilization = round((total_enrollment / total_capacity) * 100, 1) if total_capacity else 0

    # ✅ Per-session enrollment + utilization
    session_data = {}
    for s in sessions:
        # adjust this if you have a different enrollment relation
        enrolled = s.enrollment_set.count() if hasattr(s, "enrollment_set") else 0  
        session_data[s.id] = {
            "enrolled": enrolled,
            "utilization": round((enrolled / s.capacity) * 100, 1) if s.capacity else 0,
        }

    context = {
        "academy": academy,
        "programs": programs,
        "total_programs": total_programs,
        "total_sessions": total_sessions,
        "total_enrollment": total_enrollment,
        "utilization_pct": utilization,
        "revenue": 60450,  # placeholder
        "session_data": session_data,
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
    """
    Show all sessions for a given program (read-only, no enroll button).
    """
    academy = get_object_or_404(Academy, slug=academy_slug)
    program = get_object_or_404(Program, id=program_id, academy=academy)

    # fetch all sessions for this program
    sessions = (
        Session.objects.filter(program=program)
        .select_related("trainer")     # optimization
        .prefetch_related("slots")     # include schedule slots
    )

    context = {
        "academy": academy,
        "program": program,
        "sessions": sessions,
    }
    return render(request, "academies/sessions_page.html", context)

