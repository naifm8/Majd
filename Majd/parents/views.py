from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse,HttpRequest
from .models import Child
from accounts.models import ParentProfile
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from academies.models import TrainingClass

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
        emergency_contact_name = request.POST.get("emergency_contact_name", "")
        emergency_contact_phone = request.POST.get("emergency_contact_phone", "")

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
            emergency_contact_name=emergency_contact_name,
            emergency_contact_phone=emergency_contact_phone,
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
        child.emergency_contact_name = request.POST.get("emergency_contact_name", "")
        child.emergency_contact_phone = request.POST.get("emergency_contact_phone", "")

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

