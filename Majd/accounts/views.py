from django.shortcuts import render, redirect
from django.http import HttpRequest
from django.contrib.auth import login
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from .models import AcademyAdminProfile
from django.db import transaction, IntegrityError
from django.urls import reverse
from academies.models import Academy



def ensure_role_groups():
    for name in ["academy_admin", "trainer", "parent"]:
        Group.objects.get_or_create(name=name)

User = get_user_model()

ROLE_GROUPS = {"parent", "trainer", "academy_admin"}


def selection_view(request:HttpRequest):
    return render(request, "accounts/selection.html")




def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            # 🎯 Redirect based on role
            if user.groups.filter(name="academy_admin").exists():
                profile = user.academy_admin_profile

                # Ensure academy exists
                if not hasattr(profile, "academy"):
                    Academy.objects.create(
                        name=f"{user.first_name or user.username} {user.last_name or ''} Academy".strip(),
                        city="Unknown",
                        owner=profile,
                    )
                    return redirect("academies:setup")

                academy = profile.academy
                if not academy.description or not academy.city:
                    return redirect("academies:setup")

                # ✅ Academy admin → their academy detail page
                return redirect("academies:dashboard")

            elif user.groups.filter(name="trainer").exists():
                # ✅ Trainer → dashboard (replace with your trainer dashboard URL)
                return redirect("main:main_home_view")

            elif user.groups.filter(name="parent").exists():
                # ✅ Parent → academies list
                return redirect("academies:list")

            # Default: send to site home
            return redirect(reverse("main:main_home_view"))

        else:
            messages.error(request, "Invalid username or password.")

            return render(request, "accounts/login.html")

    return render(request, "accounts/login.html")


User = get_user_model()

def register_view(request):
    pre_selected_role = request.GET.get("role")
    if pre_selected_role not in {"parent", "trainer", "academy_admin"}:
        pre_selected_role = None

    if request.method == "POST":
        user_type = request.POST.get("user_type") or pre_selected_role

        if user_type not in {"parent", "trainer", "academy_admin"}:
            messages.error(request, "Invalid account type.", "alert-danger")
            return render(request, "accounts/register.html", {"pre_selected_role": pre_selected_role, "values": request.POST})

        password1 = request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")
        if password1 != password2:
            messages.error(request, "Passwords do not match.", "alert-danger")
            return render(request, "accounts/register.html", {"pre_selected_role": pre_selected_role, "values": request.POST})

        if not request.POST.get("terms"):
            messages.error(request, "You must agree to the Terms and Privacy Policy.", "alert-danger")
            return render(request, "accounts/register.html", {"pre_selected_role": pre_selected_role, "values": request.POST})

        username   = (request.POST.get("username") or "").strip()
        first_name = (request.POST.get("first_name") or "").strip()
        last_name  = (request.POST.get("last_name") or "").strip()
        email      = (request.POST.get("email") or "").strip().lower()

        if not username:
            messages.error(request, "Username is required.", "alert-danger")
            return render(request, "accounts/register.html", {"pre_selected_role": pre_selected_role, "values": request.POST})

        if User.objects.filter(username=username).exists():
            messages.error(request, "This username is already taken. Please choose another.", "alert-danger")
            return render(request, "accounts/register.html", {"pre_selected_role": pre_selected_role, "values": request.POST})


        if hasattr(User, "_meta") and any(f.name == "email" and f.unique for f in User._meta.fields):
            if email and User.objects.filter(email=email).exists():
                messages.error(request, "This email is already in use.", "alert-danger")
                return render(request, "accounts/register.html", {"pre_selected_role": pre_selected_role, "values": request.POST})


        try:
            with transaction.atomic():
                Group.objects.get_or_create(name="academy_admin")
                Group.objects.get_or_create(name="trainer")
                Group.objects.get_or_create(name="parent")

                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password1,
                    first_name=first_name,
                    last_name=last_name,
                )
                group = Group.objects.get(name=user_type)
                user.groups.add(group)

                if user_type == "trainer":
                    from accounts.models import TrainerProfile
                    TrainerProfile.objects.create(user=user)

                elif user_type == "parent":
                    from accounts.models import ParentProfile
                    ParentProfile.objects.create(user=user)

                elif user_type == "academy_admin":
                    profile = AcademyAdminProfile.objects.create(user=user)
                    academy = Academy.objects.create(
                        name=f"{user.first_name or user.username} {user.last_name or ''} Academy".strip(),
                        city="Unknown",
                        owner=profile,
                    )
                    from django.contrib.auth import login
                    login(request, user)
                    messages.success(request, "Registered successfully. Welcome to your dashboard!", "alert-success")
                    return redirect("payment:subscription_step")

                from django.contrib.auth import login
                login(request, user)
                messages.success(request, "Registered successfully.", "alert-success")
                return redirect(reverse("main:main_home_view"))

        except IntegrityError as e:
            messages.error(request, f"Database error: {e}", "alert-danger")
            return render(request, "accounts/register.html", {"pre_selected_role": pre_selected_role, "values": request.POST})

        except Group.DoesNotExist:
            messages.error(request, "Role group is missing. Please load groups fixtures or create groups in admin.", "alert-danger")
            return render(request, "accounts/register.html", {"pre_selected_role": pre_selected_role, "values": request.POST})

        except Exception as e:
            messages.error(request, f"Couldn't register user. Error: {e}", "alert-danger")
            return render(request, "accounts/register.html", {"pre_selected_role": pre_selected_role, "values": request.POST})

    
    return render(request, "accounts/register.html", {"pre_selected_role": pre_selected_role})


def log_out(request: HttpRequest):

    logout(request)
    messages.success(request, "logged out successfully", "alert-warning")

    return redirect(request.GET.get("next", "/"))

