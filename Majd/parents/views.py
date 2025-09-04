from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from datetime import date, datetime, timedelta
from django.utils import timezone
from django.db.models import Sum
from player_payments.models import PaymentTransaction, PlayerEnrollment
from player.models import PlayerProfile
from .models import Child, Enrollment
from .forms import EnrollmentForm, ParentPaymentForm
from academies.models import Academy, Session, TrainingClass, Program
from accounts.models import ParentProfile
from payment.models import SubscriptionPlan
from django.db import transaction
# Create your views here.

@login_required
def parent_dashboard_view(request):
    parent_profile = getattr(request.user, "parent_profile", None)
    if not parent_profile:
        messages.error(request, "Only parents can access this dashboard.")
        return redirect("home")

    children = parent_profile.children.all()

    # --- Stats ---
    children_count = children.count()

    today = timezone.localdate()
    week_start = today - timedelta(days=today.weekday())   # Monday
    week_end = week_start + timedelta(days=6)

    # Sessions this week for all enrolled children
    sessions_this_week = Session.objects.filter(
        enrollments__child__in=children,
        start_datetime__date__gte=week_start,
        start_datetime__date__lte=week_end,
        enrollments__is_active=True
    ).distinct()

    # Attendance avg (if PlayerProfile has attendance_rate)
    avg_attendance = 0
    if children.exists():
        rates = [
            c.player_profile.attendance_rate
            for c in children
            if hasattr(c, "player_profile")
        ]
        if rates:
            avg_attendance = round(sum(rates) / len(rates), 1)

    # Payments this month
    month_start = today.replace(day=1)
    total_payments = PaymentTransaction.objects.filter(
        enrollment__child__in=children,
        status="completed",
        created_at__date__gte=month_start
    ).aggregate(total=Sum("amount"))["total"] or 0

    # --- Payment Due ---
    payment_due = PlayerEnrollment.objects.filter(
        child__in=children,
        status="active"
    ).order_by("end_date").first()  # soonest expiring plan

    due_days, due_days_abs = None, None
    if payment_due:
        due_days = (payment_due.end_date - today).days
        due_days_abs = abs(due_days)

    # --- Recent Activity ---
    recent_activities = []
    for child in children:
        # last 3 enrollments (adjust if you track activity elsewhere)
        recent_activities += list(
            Enrollment.objects.filter(child=child).order_by("-enrolled_at")[:3]
        )

    context = {
        "children": children,
        "children_count": children_count,
        "sessions_this_week": sessions_this_week.count(),
        "avg_attendance": avg_attendance,
        "total_payments": total_payments,
        "payment_due": payment_due,
        "due_days": due_days,
        "due_days_abs": due_days_abs,
        "recent_activities": recent_activities,
    }
    return render(request, "main/overview.html", context)   



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
            return redirect("parents:dashboard")

        # Collect form data
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name", "")
        gender = request.POST.get("gender", "")
        date_of_birth = request.POST.get("date_of_birth") or None
        primary_sport = request.POST.get("primary_sport", "")
        skill_level = request.POST.get("skill_level", "beginner")
        medical_notes = request.POST.get("medical_notes", "")
        profile_image = request.FILES.get("profile_image")

        try:
            with transaction.atomic():
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

                # Create linked player profile
                PlayerProfile.objects.create(child=child)


            messages.success(request, f"Child {child.first_name} has been added successfully!")

        except Exception as e:
            messages.error(request, f"Error creating child and player profile: {str(e)}")

        return redirect("parents:children")

    return redirect("parents:dashboard")


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
        return redirect("parents:children")

    return redirect("parents:dashboard")

@login_required
def delete_child_view(request, child_id):
    child = get_object_or_404(Child, id=child_id, parent=request.user.parent_profile)

    if request.method == "POST":
        child.delete()
        messages.success(request, f"Child '{child.first_name} {child.last_name}' deleted successfully.")
        return redirect("parents:children")

    # If someone tries GET request
    messages.error(request, "Invalid request.")
    return redirect("parents:children")


@login_required
def schedule_view(request):
    schedule_items = []
    today = timezone.localdate()
    tomorrow = today + timedelta(days=1)

    selected_child_id = request.GET.get("child_id")  # 🔎 filter param

    if hasattr(request.user, "parent_profile"):
        children = request.user.parent_profile.children.all()

        if selected_child_id:
            children = children.filter(id=selected_child_id)

        for child in children:
            for enrollment in child.parent_enrollments.filter(
                is_active=True
            ).prefetch_related("sessions__program__academy", "sessions__slots"):
                for session in enrollment.sessions.all():
                    next_occurrence = None
                    if session.start_datetime and session.end_datetime:
                        current_date = max(today, session.start_datetime.date())
                        end_date = session.end_datetime.date()

                        while current_date <= end_date:
                            weekday = current_date.strftime("%a").lower()[:3]
                            slot = session.slots.filter(weekday=weekday).first()
                            if slot:
                                next_occurrence = {
                                    "date": current_date,
                                    "start_time": slot.start_time,
                                    "end_time": slot.end_time,
                                }
                                break
                            current_date += timedelta(days=1)

                    if next_occurrence:
                        schedule_items.append({
                            "child": child,
                            "session": session,
                            "academy": session.program.academy,
                            "program": session.program,
                            "next_occurrence": next_occurrence,
                        })

    # Deduplicate child-session pairs
    schedule_items = list({(i["child"].id, i["session"].id): i for i in schedule_items}.values())

    # Sort by next occurrence date + time
    schedule_items.sort(key=lambda i: (i["next_occurrence"]["date"], i["next_occurrence"]["start_time"]))

    return render(
        request,
        "main/schedule.html",
        {
            "schedule_items": schedule_items,
            "today": today,
            "tomorrow": tomorrow,
            "children": request.user.parent_profile.children.all(),
            "selected_child_id": int(selected_child_id) if selected_child_id else None,
        },
    )


@login_required
def unenroll_view(request, session_id, child_id):
    child = get_object_or_404(Child, id=child_id, parent=request.user.parent_profile)
    session = get_object_or_404(Session, id=session_id)

    # find the enrollment linking child+program
    enrollment = Enrollment.objects.filter(child=child, program=session.program).first()
    if not enrollment:
        messages.error(request, "Enrollment not found.", extra_tags="alert-danger")
        return redirect("academies:schedule_view")

    # remove session from enrollment
    enrollment.sessions.remove(session)

    # if no sessions left, deactivate enrollment
    if enrollment.sessions.count() == 0:
        enrollment.is_active = False
        enrollment.save()
        messages.success(request, f"{child.first_name} was unenrolled from {session.title}.", extra_tags="alert-success")
    else:
        messages.success(request, f"{child.first_name} was unenrolled from {session.title}.", extra_tags="alert-success")

    return redirect("parents:schedule")


@login_required
def payments_view(request):
    # Get user's parent profile
    try:
        parent_profile = request.user.parent_profile
    except:
        parent_profile = None
    
    if not parent_profile:
        return render(request, "main/payments.html", {
            "payments": [],
            "total_paid": 0,
            "outstanding": 0,
            "next_payment": {"amount": 0, "date": None},
            "upcoming": [],
            "methods": [],
            "parent_profile": None,
        })
    
    # Get real payment data from enrollments
    payments = []
    total_paid = 0
    outstanding = 0
    upcoming_payments = []
    
    for child in parent_profile.children.all():
        for enrollment in child.parent_enrollments.all():
            if enrollment.is_active:
                # Get subscription plan price
                from payment.models import SubscriptionPlan
                subscription_plan = SubscriptionPlan.objects.filter(
                    academy=enrollment.program.academy,
                    is_active=True
                ).first()
                
                price = subscription_plan.price if subscription_plan else 0
                
                # Calculate payment status
                payment_status = "not_paid"  # Default to not paid
                payment_date = enrollment.enrolled_at.strftime("%Y-%m-%d")
                
                payments.append({
                    "child": {"first_name": child.first_name, "last_name": child.last_name},
                    "description": f"{enrollment.program.title} - {enrollment.program.academy.name}",
                    "academy_name": enrollment.program.academy.name,
                    "status": payment_status,
                    "amount": price,
                    "date": payment_date,
                    "enrollment": enrollment,
                    "subscription_plan": subscription_plan,
                })
                
                if payment_status == "paid":
                    total_paid += price
                else:
                    outstanding += price
                
                # Add to upcoming payments (next month)
                from datetime import date, timedelta
                next_month = date.today() + timedelta(days=30)
                upcoming_payments.append({
                    "amount": price,
                    "date": next_month,
                    "child": child.first_name,
                    "academy": enrollment.program.academy.name,
                    "program": enrollment.program.title,
                })
    
    # Calculate next payment (sum of all upcoming)
    next_payment_amount = sum(p["amount"] for p in upcoming_payments)
    next_payment_date = upcoming_payments[0]["date"] if upcoming_payments else None
    
    # Payment methods available
    payment_methods = [
        {"name": "Credit/Debit Card", "icon": "bi-credit-card", "description": "Secure online payment"},
        {"name": "Bank Transfer", "icon": "bi-bank", "description": "Direct bank transfer"},
        {"name": "Cash Payment", "icon": "bi-cash", "description": "Pay at academy location"},
    ]
    
    # Create payment form
    payment_form = ParentPaymentForm()
    
    context = {
        "payments": payments,
        "total_paid": total_paid,
        "outstanding": outstanding,
        "next_payment": {"amount": next_payment_amount, "date": next_payment_date},
        "upcoming": upcoming_payments,
        "methods": payment_methods,
        "parent_profile": parent_profile,
        "payment_form": payment_form,
    }
    
    return render(request, "main/payments.html", context)

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
    # Get academies with subscription plan info
    academies = []
    for academy in Academy.objects.all():
        subscription_plan = SubscriptionPlan.objects.filter(
            academy=academy,
            is_active=True
        ).first()
        
        academies.append({
            "academy": academy,
            "price": subscription_plan.price if subscription_plan else 0,
            "plan_type": (
                subscription_plan.plan_type.name
                if subscription_plan and subscription_plan.plan_type
                else "No Plan"
            ),
        })
    
    programs = Program.objects.filter(academy__isnull=False)
    
    # Get user's parent profile
    parent_profile = getattr(request.user, "parent_profile", None)
    
    # Create enrollment form
    enrollment_form = EnrollmentForm(parent=parent_profile) if parent_profile else None
    
    # Build enrollments list
    enrollments = []
    if parent_profile:
        for child in parent_profile.children.all():
            for enrollment in child.parent_enrollments.all():
                if enrollment.is_active:
                    subscription_plan = SubscriptionPlan.objects.filter(
                        academy=enrollment.program.academy,
                        is_active=True
                    ).first()
                    
                    price = subscription_plan.price if subscription_plan else 0
                    
                    enrollments.append({
                        "id": enrollment.id,
                        "academy": enrollment.program.academy,
                        "program": enrollment.program.title,
                        "location": getattr(enrollment.program.academy, "city", "-"),
                        "children": f"{child.first_name} {child.last_name}".strip(),
                        "features": [enrollment.program.sport_type.title()],
                        "status": "Active" if enrollment.is_active else "Inactive",
                        "price": price,
                        "next_payment": date.today(),
                        "enrollment": enrollment,
                        "child": child,
                    })
    
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
        "form": enrollment_form,
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
def process_payment(request):
    """Process payment for an enrollment"""
    if request.method == "POST":
        try:
            enrollment_id = request.POST.get('enrollment_id')
            payment_method = request.POST.get('payment_method', 'card')
            amount = request.POST.get('amount')
            
            if not all([enrollment_id, amount]):
                return JsonResponse({"success": False, "error": "Missing required payment information"})
            
            # Get the enrollment
            enrollment = get_object_or_404(Enrollment, id=enrollment_id)
            
            # Verify the enrollment belongs to the user's child
            if enrollment.child.parent != request.user.parent_profile:
                return JsonResponse({"success": False, "error": "Unauthorized"})
            
            # Get subscription plan for pricing verification
            from payment.models import SubscriptionPlan
            subscription_plan = SubscriptionPlan.objects.filter(
                academy=enrollment.program.academy,
                is_active=True
            ).first()
            
            if not subscription_plan:
                return JsonResponse({"success": False, "error": "No subscription plan found for this academy"})
            
            # Calculate expected total with VAT (15%) - using same rounding as frontend
            base_price = float(subscription_plan.price)
            vat_amount = round(base_price * 0.15, 2)  # Round to 2 decimal places
            expected_total = round(base_price + vat_amount, 2)  # Round to 2 decimal places
            
            # Debug logging
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Payment calculation - Base: {base_price}, VAT: {vat_amount}, Expected Total: {expected_total}, Received: {amount}")
            
            # Verify amount matches expected total (base price + VAT)
            if abs(float(amount) - expected_total) > 0.01:  # Allow for small rounding differences
                return JsonResponse({"success": False, "error": f"Payment amount does not match expected total. Expected: SAR {expected_total:.2f}, Received: SAR {amount}"})
            
            # Create payment record (you can extend this with your payment gateway)
            from player_payments.models import PaymentTransaction, PlayerEnrollment
            
            # Create or get player enrollment
            # First, we need to find or create a PlayerSubscription for this academy
            from player_payments.models import PlayerSubscription
            player_subscription, created = PlayerSubscription.objects.get_or_create(
                academy=enrollment.program.academy,
                defaults={
                    'title': f"{enrollment.program.academy.name} Subscription",
                    'price': subscription_plan.price,
                    'billing_type': '3m',  # Default to 3 months
                    'description': f"Subscription for {enrollment.program.academy.name}",
                }
            )
            
            # Log the subscription creation/retrieval
            logger.info(f"PlayerSubscription {'created' if created else 'found'}: {player_subscription.id} for academy {enrollment.program.academy.name}")
            
            # Now create the PlayerEnrollment with the subscription
            player_enrollment, created = PlayerEnrollment.objects.get_or_create(
                subscription=player_subscription,
                child=enrollment.child,
                parent=request.user,
                start_date=date.today(),
                defaults={
                    'status': 'active',
                    'payment_method': payment_method,
                    'end_date': date.today() + timedelta(days=30),
                    'amount_paid': amount,  # This is the total amount including VAT
                    'payment_date': timezone.now(),
                }
            )
            
            # Log the enrollment creation/retrieval
            logger.info(f"PlayerEnrollment {'created' if created else 'found'}: {player_enrollment.id} for child {enrollment.child.first_name}")
            
            # Create payment transaction
            transaction = PaymentTransaction.objects.create(
                enrollment=player_enrollment,
                transaction_type='initial',
                status='completed',
                amount=amount,
                currency='SAR',
                processed_at=timezone.now(),
                notes=f'Payment for {enrollment.program.title} at {enrollment.program.academy.name}'
            )
            
            # Update enrollment status to paid
            enrollment.is_active = True  # Keep enrollment active after payment
            
            # Send invoice email to parent
            from .utils import send_payment_invoice_email
            email_sent = send_payment_invoice_email(transaction, player_enrollment, request.user)
            
            # Log the email sending result for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Payment processed for {enrollment.child.first_name}. Email sent: {email_sent}. Parent email: {request.user.email}")
            
            success_message = f"Payment of SAR {amount} processed successfully for {enrollment.child.first_name}"
            if email_sent:
                success_message += ". An invoice has been sent to your email."
            else:
                success_message += ". Note: Invoice email could not be sent."
            
            messages.success(request, success_message)
            return JsonResponse({"success": True, "transaction_id": transaction.id, "email_sent": email_sent})
            
        except Exception as e:
            # Log the error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Payment processing error: {str(e)}")
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

@login_required
def edit_profile_view(request):
    if request.method == "POST":
        user = request.user
        parent_profile = getattr(user, "parent_profile", None)

        # Update User fields
        user.first_name = request.POST.get("first_name", user.first_name)
        user.last_name = request.POST.get("last_name", user.last_name)
        user.email = request.POST.get("email", user.email)
        user.save()

        # Update ParentProfile fields
        if parent_profile:
            parent_profile.phone = request.POST.get("phone", parent_profile.phone)
            parent_profile.location = request.POST.get("location", parent_profile.location)
            parent_profile.save()

        messages.success(request, "Profile updated successfully.", extra_tags="alert-success")
        return redirect("parents:settings")  # adjust to your settings URL

    return redirect("parents:settings")


