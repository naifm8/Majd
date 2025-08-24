from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse, Http404
from django.contrib.auth import login
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from .models import TrainerProfile, ParentProfile, AcademyAdminProfile, Child
from django.db import transaction, IntegrityError
from django.urls import reverse

from .models import AcademyAdminProfile, TrainerProfile, ParentProfile


User = get_user_model()

ROLE_GROUPS = {"parent", "trainer", "academy_admin"}


def selection_view(request:HttpRequest):
    return render(request, "accounts/selection.html")



def login_view(request: HttpRequest):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            messages.success(request, "Logged in successfully", "alert-success")
            return redirect(request.GET.get("next", "/"))
        else:
            messages.error(request, "Please try again. Your credentials are wrong", "alert-danger")

    return render(request, "accounts/login.html")




def register_view(request: HttpRequest):

    pre_selected_role = request.GET.get("role")
    if pre_selected_role not in ROLE_GROUPS:
        pre_selected_role = None

    if request.method == "POST":
        user_type = request.POST.get("user_type") or pre_selected_role


        if user_type not in ROLE_GROUPS:
            messages.error(request, "Invalid account type.", "alert-danger")
            return render(request, "accounts/register.html", {"pre_selected_role": pre_selected_role, "values": request.POST})


        password1 = request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")
        if password1 != password2:
            messages.error(request, "Passwords do not match.", "alert-danger")
            return render(request, "accounts/register.html",{"pre_selected_role": pre_selected_role, "values": request.POST})


        if not request.POST.get("terms"):
            messages.error(request, "You must agree to the Terms and Privacy Policy.", "alert-danger")
            return render(request, "accounts/register.html", {"pre_selected_role": pre_selected_role, "values": request.POST})


        username   = request.POST.get("username", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name  = request.POST.get("last_name", "").strip()
        email      = request.POST.get("email", "").strip().lower()

        try:
            with transaction.atomic():
                user = User.objects.create_user(username=username, email=email, password=password1, first_name=first_name, last_name=last_name,)
                group = Group.objects.get(name=user_type)
                user.groups.add(group)

                if user_type == "trainer":
                    TrainerProfile.objects.create(user=user)
                elif user_type == "parent":
                    ParentProfile.objects.create(user=user)
                else: 
                    AcademyAdminProfile.objects.create(user=user)

            login(request, user)
            messages.success(request, "Registered User Successfuly", "alert-success")
            return redirect(reverse("main:main_home_view"))

        except IntegrityError:
            messages.error(request, "Please choose another username", "alert-danger")
            return render(request, "accounts/register.html",
                          {"pre_selected_role": pre_selected_role, "values": request.POST})
        except Exception:
            messages.error(request, "Couldn't register user. Try again", "alert-danger")
            return render(request, "accounts/register.html",
                          {"pre_selected_role": pre_selected_role, "values": request.POST})

    return render(request, "accounts/register.html", {"pre_selected_role": pre_selected_role})


def log_out(request: HttpRequest):

    logout(request)
    messages.success(request, "logged out successfully", "alert-warning")

    return redirect(request.GET.get("next", "/"))

def ensure_role_groups():
    for name in ["academy_admin", "trainer", "parent"]:
        Group.objects.get_or_create(name=name)