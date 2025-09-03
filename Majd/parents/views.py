from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from datetime import date, datetime, timedelta
from django.utils import timezone

from player.models import PlayerProfile
from .models import Child, Enrollment, ParentSubscription
from .forms import EnrollmentForm, ParentPaymentForm
from academies.models import Academy, TrainingClass, Program
from accounts.models import ParentProfile
from payment.models import SubscriptionPlan
from django.db import transaction
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
    # Debug: Check what data we have
    academies_count = Academy.objects.count()
    subscription_plans_count = SubscriptionPlan.objects.count()
    print(f"DEBUG: Found {academies_count} academies and {subscription_plans_count} subscription plans")
    
    # Check if we're redirecting from enrollment (specific academy needed)
    required_academy_slug = request.GET.get('academy')
    required_academy = None
    if required_academy_slug:
        try:
            required_academy = Academy.objects.get(slug=required_academy_slug)
            print(f"DEBUG: Parent needs to subscribe to: {required_academy.name}")
        except Academy.DoesNotExist:
            print(f"DEBUG: Academy with slug '{required_academy_slug}' not found")
    
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
                subscription_plan = SubscriptionPlan.objects.filter(
                    academy=enrollment.program.academy,
                    is_active=True
                ).first()
                
                price = subscription_plan.price if subscription_plan else 0
                
                # Get payment status from enrollment model
                payment_status = enrollment.payment_status
                payment_date = enrollment.enrolled_at.strftime("%Y-%m-%d")
                
                # Use payment_date if available
                if enrollment.payment_date:
                    payment_date = enrollment.payment_date.strftime("%Y-%m-%d")
                
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
    
    # Get available subscription plans for parents to subscribe to
    available_subscription_plans = []
    all_academies = Academy.objects.all()
    print(f"DEBUG: Processing {all_academies.count()} academies for subscription plans")
    
    for academy in all_academies:
        print(f"DEBUG: Processing academy: {academy.name} (slug: {academy.slug})")
        
        subscription_plan = SubscriptionPlan.objects.filter(
            academy=academy,
            is_active=True
        ).first()
        
        if not subscription_plan:
            subscription_plan = SubscriptionPlan.objects.filter(
                academy=academy
            ).first()
        
        print(f"DEBUG: Found subscription plan: {subscription_plan}")
        
        # Check if this is the required academy
        is_required = required_academy and academy.id == required_academy.id
        
        if subscription_plan:
            available_subscription_plans.append({
                "academy": academy,
                "subscription_plan": subscription_plan,
                "price": subscription_plan.price,
                "plan_type": subscription_plan.plan_type.name if subscription_plan.plan_type else "Basic Plan",
                "is_required": is_required
            })
        else:
            # Add academy even without subscription plan for debugging
            available_subscription_plans.append({
                "academy": academy,
                "subscription_plan": None,
                "price": 100.00,  # Default price
                "plan_type": "No Plan Available",
                "is_required": is_required
            })
    
    # Sort to put required academy first
    if required_academy:
        available_subscription_plans.sort(key=lambda x: not x.get('is_required', False))
    
    print(f"DEBUG: Created {len(available_subscription_plans)} subscription plan entries")

    context = {
        "payments": payments,
        "total_paid": total_paid,
        "outstanding": outstanding,
        "next_payment": {"amount": next_payment_amount, "date": next_payment_date},
        "upcoming": upcoming_payments,
        "methods": payment_methods,
        "parent_profile": parent_profile,
        "payment_form": payment_form,
        "available_subscription_plans": available_subscription_plans,
        "required_academy": required_academy,
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
    # Get real academies and programs from database with pricing
    academies = []
    for academy in Academy.objects.all():
        # Get the subscription plan for this academy
        subscription_plan = SubscriptionPlan.objects.filter(
            academy=academy,
            is_active=True
        ).first()
        
        # If no active subscription plan, try to get any subscription plan
        if not subscription_plan:
            subscription_plan = SubscriptionPlan.objects.filter(
                academy=academy
            ).first()
        
        academies.append({
            "academy": academy,
            "price": subscription_plan.price if subscription_plan else 100.00,  # Default price
            "plan_type": subscription_plan.plan_type.name if subscription_plan and subscription_plan.plan_type else "Basic Plan"
        })
    
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
                    # Get the subscription plan price for this program
                    subscription_plan = SubscriptionPlan.objects.filter(
                        academy=enrollment.program.academy,
                        is_active=True
                    ).first()
                    
                    price = subscription_plan.price if subscription_plan else 0
                    
                    enrollments.append({
                        "id": enrollment.id,
                        "academy": enrollment.program.academy,
                        "program": enrollment.program.title,
                        "location": enrollment.program.academy.city,
                        "children": f"{child.first_name} {child.last_name}".strip(),
                        "features": [enrollment.program.sport_type.title()],
                        "status": "Active" if enrollment.is_active else "Inactive",
                        "price": price,
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
def process_payment(request):
    """Process payment for an enrollment"""
    if request.method == "POST":
        try:
            enrollment_id = request.POST.get('enrollment_id')
            payment_method = request.POST.get('payment_method', 'card')
            amount = request.POST.get('amount')
            
            if not amount:
                return JsonResponse({"success": False, "error": "Missing required payment information"})
            
            # Check if this is a new subscription (no enrollment_id) or existing enrollment payment
            is_new_subscription = not enrollment_id
            
            if is_new_subscription:
                # This is a new academy subscription payment
                # We need to get the academy from the payment form or session
                academy_slug = request.POST.get('academy_slug')
                if not academy_slug:
                    return JsonResponse({"success": False, "error": "Academy information missing"})
                
                try:
                    academy = Academy.objects.get(slug=academy_slug)
                except Academy.DoesNotExist:
                    return JsonResponse({"success": False, "error": "Academy not found"})
                
                # Get subscription plan for this academy
                subscription_plan = SubscriptionPlan.objects.filter(
                    academy=academy,
                    is_active=True
                ).first()
                
                if not subscription_plan:
                    subscription_plan = SubscriptionPlan.objects.filter(
                        academy=academy
                    ).first()
                
                if not subscription_plan:
                    return JsonResponse({"success": False, "error": "No subscription plan found for this academy"})
                
                # For new subscriptions, we don't have an enrollment yet
                enrollment = None
                
            else:
                # This is a payment for an existing enrollment
                enrollment = get_object_or_404(Enrollment, id=enrollment_id)
                
                # Verify the enrollment belongs to the user's child
                if enrollment.child.parent != request.user.parent_profile:
                    return JsonResponse({"success": False, "error": "Unauthorized"})
                
                # Get subscription plan for pricing verification
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
            
            if is_new_subscription:
                # This is a new academy subscription - create ParentSubscription
                parent_subscription, created = ParentSubscription.objects.get_or_create(
                    parent=request.user.parent_profile,
                    academy=academy,
                    defaults={
                        'is_active': True,
                        'start_date': timezone.now(),
                        'end_date': timezone.now() + timedelta(days=30),
                        'subscription_type': 'monthly',
                        'amount_paid': amount,
                    }
                )
                
                # Update existing subscription if it already exists
                if not created:
                    parent_subscription.is_active = True
                    parent_subscription.end_date = timezone.now() + timedelta(days=30)
                    parent_subscription.amount_paid = amount
                    parent_subscription.save()
                
                # For academy subscriptions, we don't need PlayerEnrollment or PaymentTransaction
                # The ParentSubscription record is sufficient for tracking the subscription
                player_enrollment = None
                transaction = None
                
            else:
                # This is a payment for an existing enrollment
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
            
            # Update enrollment status to paid (only for existing enrollments)
            if not is_new_subscription:
                enrollment.is_active = True  # Keep enrollment active after payment
                enrollment.payment_status = 'paid'  # Mark as paid
                enrollment.payment_date = timezone.now()  # Set payment date
                enrollment.save()
            
            # Send invoice email to parent (only for existing enrollments with transactions)
            email_sent = False
            if transaction and player_enrollment:
                from .utils import send_payment_invoice_email
                email_sent = send_payment_invoice_email(transaction, player_enrollment, request.user)
            
            # Log the email sending result for debugging
            import logging
            logger = logging.getLogger(__name__)
            
            if is_new_subscription:
                logger.info(f"Academy subscription processed for {academy.name}. Email sent: {email_sent}. Parent email: {request.user.email}")
                success_message = f"Academy subscription of SAR {amount} processed successfully for {academy.name}"
                if email_sent:
                    success_message += ". An invoice has been sent to your email."
                else:
                    success_message += ". Note: Invoice email could not be sent."
                
                # Return success with redirect information
                return JsonResponse({
                    "success": True, 
                    "subscription_created": True, 
                    "email_sent": email_sent,
                    "redirect_url": f"/academies/{academy.slug}/",
                    "message": success_message
                })
            else:
                logger.info(f"Payment processed for {enrollment.child.first_name}. Email sent: {email_sent}. Parent email: {request.user.email}")
                success_message = f"Payment of SAR {amount} processed successfully for {enrollment.child.first_name}"
                if email_sent:
                    success_message += ". An invoice has been sent to your email."
                else:
                    success_message += ". Note: Invoice email could not be sent."
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


