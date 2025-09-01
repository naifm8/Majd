from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from datetime import date, datetime
from .models import Child, Enrollment
from .forms import EnrollmentForm
from academies.models import Academy, TrainingClass, Program
from accounts.models import ParentProfile

# Create your views here.

@login_required
def dashboard_view(request):
    parent = get_object_or_404(ParentProfile, user=request.user)
    children = parent.children.with_age()

    return render(request, "main/overview.html", {
        'parent': parent,
        'children': children,
        'children_count': children.count(),
    })


@login_required
def my_children_view(request):

    parent = get_object_or_404(ParentProfile, user=request.user)
    children = parent.children.with_age()

    return render(request, "main/my_children.html", {
        "parent": parent,
        "children": children,
    })



@login_required
def add_child_view(request):
    if request.method == "POST":
        parent_profile = getattr(request.user, "parent_profile", None)

        if not parent_profile:
            messages.error(request, "You must be a parent to add a child.")
            return redirect("parents:dashboard_view")

        # Collect form data
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name", "")
        gender = request.POST.get("gender", "")
        date_of_birth = request.POST.get("date_of_birth") or None
        primary_sport = request.POST.get("primary_sport", "")
        skill_level = request.POST.get("skill_level", "beginner")
        medical_notes = request.POST.get("medical_notes", "")


        profile_image = request.FILES.get("profile_image")

        # Create the child
        child = Child.objects.create(
            parent=parent_profile,
            first_name=first_name,
            last_name=last_name,
            gender=gender,
            date_of_birth=date_of_birth,
            primary_sport=primary_sport,
            skill_level=skill_level,
            medical_notes=medical_notes,
            profile_image=profile_image if profile_image else "images/profileImage/profileImage.webp"
        )

        messages.success(request, f"Child {child.first_name} has been added successfully!")
        return redirect("parents:my_children_view")

    return redirect("parents:dashboard_view")


@login_required
def edit_child_view(request, child_id):
    child = get_object_or_404(Child, id=child_id, parent=request.user.parent_profile)

    if request.method == "POST":
        child.first_name = request.POST.get("first_name")
        child.last_name = request.POST.get("last_name", "")
        child.gender = request.POST.get("gender", "")
        child.date_of_birth = request.POST.get("date_of_birth") or None
        child.primary_sport = request.POST.get("primary_sport", "")
        child.skill_level = request.POST.get("skill_level", "beginner")
        child.medical_notes = request.POST.get("medical_notes", "")


        if "profile_image" in request.FILES:
            child.profile_image = request.FILES["profile_image"]

        child.save()
        messages.success(request, f"{child.first_name}'s profile has been updated.")
        return redirect("parents:my_children_view")

    return redirect("parents:dashboard_view")

@login_required
def delete_child_view(request, child_id):
    child = get_object_or_404(Child, id=child_id, parent=request.user.parent_profile)

    if request.method == "POST":
        child.delete()
        messages.success(request, f"Child '{child.first_name} {child.last_name}' deleted successfully.")
        return redirect("parents:my_children_view")

    # If someone tries GET request
    messages.error(request, "Invalid request.")
    return redirect("parents:my_children_view")


@login_required
def schedule_view(request):
    schedule_items = []

    if hasattr(request.user, "parent_profile"):
        children = request.user.parent_profile.children.all()

        for child in children:
            classes = TrainingClass.objects.filter(
                session__program__children=child
            ).order_by("date", "start_time")

            for c in classes:
                schedule_items.append({
                    "child": child,
                    "class": c
                })

    # Sort all sessions across children by date/time
    schedule_items = sorted(schedule_items, key=lambda x: (x["class"].date, x["class"].start_time))

    return render(request, "main/schedule.html", {"schedule_items": schedule_items})

@login_required
def payments_view(request):
    
    # hard coded data for view the frontend
    payments = [
        {"child": {"first_name": "Alex", "last_name": "Johnson"},
         "description": "Monthly Training Fee",
         "academy_name": "Elite Soccer Academy",
         "status": "paid",
         "amount": 150,
         "date": "2024-03-01"},
        {"child": {"first_name": "Emma", "last_name": "Johnson"},
         "description": "Swimming Lessons",
         "academy_name": "AquaLife Swimming",
         "status": "paid",
         "amount": 120,
         "date": "2024-03-01"},
    ]

    return render(request, "main/payments.html", {
        "payments": payments,
        "total_paid": 345,
        "outstanding": 75,
        "next_payment": {"amount": 270, "date": "2024-04-01"},
        "upcoming": [],
        "methods": [],
    })

@login_required
def reports_view(request):
    parent = getattr(request.user, "parent_profile", None)

    if not parent:
        return render(request, "reports/reports.html", {"reports": []})

    # Fetch all children of this parent
    children = Child.objects.filter(parent=parent)

    reports = []
    for child in children:
        # if child has a linked player_profile, use attendance/progress
        player_profile = getattr(child, "player_profile", None)

        reports.append({
            "child": child,
            "academy_name": (
                player_profile.academy.name if player_profile and player_profile.academy else "Not Assigned"
            ),
            "grade": player_profile.current_grade if player_profile else None,
            "overall_progress": player_profile.avg_progress if player_profile else 0,
            "attendance_rate": player_profile.attendance_rate if player_profile else 0,
            # For demo purposes — you could fetch these from models later
            "strengths": ["Speed", "Team Work", "Leadership"] if child.first_name == "Alex" else ["Freestyle", "Butterfly"],
            "areas_for_improvement": ["Ball Control", "Defensive Positioning"] if child.first_name == "Alex" else ["Endurance"],
            "last_report": date.today(),
        })

    return render(request, "main/reports.html", {"reports": reports})



@login_required
def subscriptions_view(request):
    # Get real academies and programs from database
    academies = Academy.objects.all()
    programs = Program.objects.filter(academy__isnull=False)
    
    # Get user's parent profile
    try:
        parent_profile = request.user.parent_profile
    except:
        parent_profile = None
    
    # Create enrollment form
    enrollment_form = EnrollmentForm(parent=parent_profile) if parent_profile else None
    
    # Get real enrollments if parent profile exists
    if parent_profile:
        enrollments = []
        for child in parent_profile.children.all():
            for enrollment in child.parent_enrollments.all():
                if enrollment.is_active:
                    enrollments.append({
                        "id": enrollment.id,
                        "academy": enrollment.program.academy,
                        "program": enrollment.program.title,
                        "location": enrollment.program.academy.city,
                        "children": f"{child.first_name} {child.last_name}".strip(),
                        "features": [enrollment.program.sport_type.title()],
                        "status": "Active" if enrollment.is_active else "Inactive",
                        "price": 0,  # You can add pricing later
                        "next_payment": date.today(),
                        "enrollment": enrollment,
                        "child": child,
                    })
    else:
        enrollments = []
    
    # Calculate totals
    total_subscriptions = len(enrollments)
    active_subscriptions = sum(1 for e in enrollments if e["status"] == "Active")
    monthly_spend = sum(e.get("price", 0) for e in enrollments if e["status"] == "Active")

    context = {
        "enrollments": enrollments,
        "academies": academies,
        "programs": programs,
        "total_subscriptions": total_subscriptions,
        "active_subscriptions": active_subscriptions,
        "monthly_spend": monthly_spend,
        "parent_profile": parent_profile,
        "form": enrollment_form,  # Add the form to context
    }
    return render(request, "main/subscriptions.html", context)


@login_required
@require_POST
def enroll_child(request):
    """Handle child enrollment in a program"""
    if request.method == "POST":
        try:
            parent_profile = request.user.parent_profile
            if not parent_profile:
                return JsonResponse({"success": False, "error": "Parent profile not found"})
            
            form = EnrollmentForm(request.POST, parent=parent_profile)
            if form.is_valid():
                # Check if enrollment already exists
                existing_enrollment = Enrollment.objects.filter(
                    child=form.cleaned_data['child'],
                    program=form.cleaned_data['program']
                ).first()
                
                if existing_enrollment:
                    if existing_enrollment.is_active:
                        return JsonResponse({"success": False, "error": "Child is already enrolled in this program"})
                    else:
                        # Reactivate existing enrollment
                        existing_enrollment.is_active = True
                        existing_enrollment.save()
                        messages.success(request, f"Successfully re-enrolled {form.cleaned_data['child'].first_name} in {form.cleaned_data['program'].title}")
                else:
                    # Create new enrollment
                    enrollment = form.save(commit=False)
                    enrollment.save()
                    messages.success(request, f"Successfully enrolled {form.cleaned_data['child'].first_name} in {form.cleaned_data['program'].title}")
                
                return JsonResponse({"success": True})
            else:
                return JsonResponse({"success": False, "error": "Invalid form data"})
                
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    
    return JsonResponse({"success": False, "error": "Invalid request method"})


@login_required
@require_POST
def pause_enrollment(request, enrollment_id):
    """Pause an active enrollment"""
    try:
        enrollment = get_object_or_404(Enrollment, id=enrollment_id)
        
        # Check if the enrollment belongs to the user's child
        if enrollment.child.parent != request.user.parent_profile:
            return JsonResponse({"success": False, "error": "Unauthorized"})
        
        enrollment.is_active = False
        enrollment.save()
        
        messages.success(request, f"Enrollment paused for {enrollment.child.first_name}")
        return JsonResponse({"success": True})
        
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@login_required
@require_POST
def resume_enrollment(request, enrollment_id):
    """Resume a paused enrollment"""
    try:
        enrollment = get_object_or_404(Enrollment, id=enrollment_id)
        
        # Check if the enrollment belongs to the user's child
        if enrollment.child.parent != request.user.parent_profile:
            return JsonResponse({"success": False, "error": "Unauthorized"})
        
        enrollment.is_active = True
        enrollment.save()
        
        messages.success(request, f"Enrollment resumed for {enrollment.child.first_name}")
        return JsonResponse({"success": True})
        
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})




@login_required
def settings_view(request):
    """
    Render the settings page with tabs: Profile, Notifications, Privacy, Account.
    """
    
    context = {
        "user": request.user,
    }
    return render(request, "main/settings.html", context)


