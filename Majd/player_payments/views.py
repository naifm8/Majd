from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.utils.decorators import method_decorator
from django.utils import timezone
from datetime import timedelta
from .models import PlayerSubscription, PlayerEnrollment, PaymentTransaction
from academies.models import Academy, Program
from parents.models import Child


class PlayerSubscriptionListView(ListView):
    """List all available player subscriptions by academy"""
    model = PlayerSubscription
    template_name = 'player_payments/subscription_list.html'
    context_object_name = 'subscriptions'
    
    def get_queryset(self):
        queryset = PlayerSubscription.objects.filter(is_active=True).select_related('academy', 'program')
        
        # Filter by academy if specified
        academy_id = self.request.GET.get('academy')
        if academy_id:
            queryset = queryset.filter(academy_id=academy_id)
            
        # Filter by program/sport if specified
        sport = self.request.GET.get('sport')
        if sport:
            queryset = queryset.filter(program__sport_type=sport)
            
        return queryset.order_by('academy__name', 'price')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['academies'] = Academy.objects.all()
        context['sport_choices'] = Program.SportType.choices
        context['selected_academy'] = self.request.GET.get('academy', '')
        context['selected_sport'] = self.request.GET.get('sport', '')
        return context


class PlayerSubscriptionDetailView(DetailView):
    """Show detailed view of a subscription plan"""
    model = PlayerSubscription
    template_name = 'player_payments/subscription_detail.html'
    context_object_name = 'subscription'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add user's children if logged in as parent
        if self.request.user.is_authenticated and hasattr(self.request.user, 'parent_profile'):
            context['children'] = self.request.user.parent_profile.children.all()
            
        # Add enrollment status for each child
        if 'children' in context:
            subscription = self.object
            for child in context['children']:
                # Check if child has active enrollment for this subscription
                active_enrollment = PlayerEnrollment.objects.filter(
                    subscription=subscription,
                    child=child,
                    status='active',
                    end_date__gte=timezone.now().date()
                ).first()
                child.current_enrollment = active_enrollment
                
        return context


@method_decorator(login_required, name='dispatch')
class EnrollmentView(DetailView):
    """Handle subscription enrollment for a specific child"""
    model = PlayerSubscription
    template_name = 'player_payments/enrollment_form.html'
    context_object_name = 'subscription'
    
    def dispatch(self, request, *args, **kwargs):
        # Ensure user is a parent
        if not hasattr(request.user, 'parent_profile'):
            messages.error(request, "You must be a parent to enroll children in programs.")
            return redirect('main:main_home_view')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get child ID from URL
        child_id = self.kwargs.get('child_id')
        if child_id:
            context['child'] = get_object_or_404(
                Child, 
                id=child_id, 
                parent=self.request.user.parent_profile
            )
            
            # Check for existing enrollments
            existing_enrollment = PlayerEnrollment.objects.filter(
                subscription=self.object,
                child=context['child'],
                status__in=['pending', 'active']
            ).first()
            context['existing_enrollment'] = existing_enrollment
            
        return context
    
    def post(self, request, *args, **kwargs):
        subscription = self.get_object()
        child_id = self.kwargs.get('child_id')
        
        if not child_id:
            messages.error(request, "Child not specified.")
            return redirect('player_payments:subscription_detail', pk=subscription.pk)
            
        child = get_object_or_404(Child, id=child_id, parent=request.user.parent_profile)
        
        # Check for existing active enrollment
        existing = PlayerEnrollment.objects.filter(
            subscription=subscription,
            child=child,
            status__in=['pending', 'active']
        ).first()
        
        if existing:
            messages.warning(request, f"{child.first_name} is already enrolled in this program.")
            return redirect('player_payments:enrollment_detail', pk=existing.pk)
        
        # Calculate enrollment period based on billing type
        start_date = timezone.now().date()
        if subscription.billing_type == '3m':
            end_date = start_date + timedelta(days=90)
        elif subscription.billing_type == '6m':
            end_date = start_date + timedelta(days=180)
        else:  # 12m
            end_date = start_date + timedelta(days=365)
        
        # Get payment method from form
        payment_method = request.POST.get('payment_method', 'card')
        auto_renewal = request.POST.get('auto_renewal', False) == 'on'
        
        # Create enrollment
        enrollment = PlayerEnrollment.objects.create(
            subscription=subscription,
            child=child,
            parent=request.user,
            start_date=start_date,
            end_date=end_date,
            amount_paid=subscription.price,
            payment_method=payment_method,
            auto_renewal=auto_renewal,
        )
        
        # Create initial payment transaction
        transaction = PaymentTransaction.objects.create(
            enrollment=enrollment,
            transaction_type='initial',
            amount=subscription.price,
        )
        
        messages.success(request, f"Enrollment created for {child.first_name}. Please complete payment.")
        return redirect('player_payments:enrollment_detail', pk=enrollment.pk)


@method_decorator(login_required, name='dispatch')
class EnrollmentDetailView(DetailView):
    """Show enrollment details and payment status"""
    model = PlayerEnrollment
    template_name = 'player_payments/enrollment_detail.html'
    context_object_name = 'enrollment'
    
    def get_queryset(self):
        # Ensure user can only view their own children's enrollments
        if hasattr(self.request.user, 'parent_profile'):
            return PlayerEnrollment.objects.filter(parent=self.request.user)
        return PlayerEnrollment.objects.none()


@login_required
def my_enrollments_view(request):
    """List all enrollments for the current parent's children"""
    if not hasattr(request.user, 'parent_profile'):
        messages.error(request, "You must be a parent to view enrollments.")
        return redirect('main:main_home_view')
    
    enrollments = PlayerEnrollment.objects.filter(
        parent=request.user
    ).select_related('subscription', 'child').order_by('-created_at')
    
    context = {
        'enrollments': enrollments,
        'active_enrollments': enrollments.filter(status='active'),
        'pending_enrollments': enrollments.filter(status='pending'),
    }
    
    return render(request, 'player_payments/my_enrollments.html', context)


@login_required
def complete_payment_view(request, enrollment_id):
    """Handle payment completion for an enrollment"""
    enrollment = get_object_or_404(
        PlayerEnrollment, 
        id=enrollment_id, 
        parent=request.user,
        status='pending'
    )
    
    if request.method == 'POST':
        # In a real implementation, you would integrate with a payment gateway here
        # For now, we'll simulate payment completion
        
        payment_method = request.POST.get('payment_method', enrollment.payment_method)
        transaction_id = request.POST.get('transaction_id', '')
        
        # Update enrollment status
        enrollment.status = 'active'
        enrollment.payment_date = timezone.now()
        enrollment.transaction_id = transaction_id
        enrollment.save()
        
        # Update transaction
        transaction = enrollment.transactions.filter(status='pending').first()
        if transaction:
            transaction.status = 'completed'
            transaction.processed_at = timezone.now()
            transaction.gateway_transaction_id = transaction_id
            transaction.save()
        
        messages.success(request, f"Payment completed! {enrollment.child.first_name} is now enrolled.")
        return redirect('player_payments:enrollment_detail', pk=enrollment.pk)
    
    context = {
        'enrollment': enrollment,
        'amount': enrollment.amount_paid,
    }
    
    return render(request, 'player_payments/complete_payment.html', context)


def academy_subscriptions_view(request, academy_id):
    """View subscriptions for a specific academy"""
    academy = get_object_or_404(Academy, id=academy_id)
    subscriptions = PlayerSubscription.objects.filter(
        academy=academy, 
        is_active=True
    ).select_related('program')
    
    context = {
        'academy': academy,
        'subscriptions': subscriptions,
    }
    
    return render(request, 'player_payments/academy_subscriptions.html', context)

