from .models import Academy
from django.views.generic import DetailView, TemplateView
from django.shortcuts import render
from .models import Academy, Program
from parents.models import Child
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from .forms import AcademyForm
from django.utils.decorators import method_decorator


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


class AcademyDetailView(DetailView):
    model = Academy
    template_name = "academies/academy_detail.html"
    context_object_name = "academy"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        academy = self.object

        # Years of Experience
        current_year = timezone.now().year
        years_experience = max(0, current_year - academy.establishment_year)

        # Active Students
        active_students = Child.objects.filter(
            programs__academy=academy
        ).distinct().count()

        context["programs"] = academy.programs.all()
        context["coaches"] = getattr(academy, "coaches", []).all() if hasattr(academy, "coaches") else []
        context["active_students"] = active_students
        context["fake_rating"] = 4.8 
        context["years_experience"] = years_experience
        return context
    

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





@method_decorator(login_required, name="dispatch")
class AcademyDashboardView(TemplateView):
    template_name = "academies/dashboard_overview.html"

    def dispatch(self, request, *args, **kwargs):
        # Ensure logged in user is academy admin
        if not hasattr(request.user, "academy_admin_profile"):
            messages.error(request, "You must be an Academy Admin to access the dashboard.")
            return redirect("main:main_home_view")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        academy = self.request.user.academy_admin_profile.academy
        context["academy"] = academy
        return context
