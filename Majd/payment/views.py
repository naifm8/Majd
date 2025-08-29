from django.views.generic import ListView, DetailView
from django.views.generic.edit import FormView
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.contrib import messages
from django.db import transaction
from datetime import timedelta
from .models import PlanType, SubscriptionPlan, Subscription
from .forms import CheckoutForm

class PlanTypeListView(ListView):
    model = PlanType
    context_object_name = "plan_types"
    template_name = "payment/plan_type_list.html"
    queryset = PlanType.objects.all().order_by('display_order')

    def get_context_data(self, **kwargs):
        """Add debug information to context"""
        context = super().get_context_data(**kwargs)
        context['debug'] = self.request.GET.get('debug') == '1'  # ?debug=1 to show debug info
        context['total_plans'] = context['plan_types'].count()
        
        # Additional debug info
        if context['debug']:
            try:
                from django.db import connection
                context['db_info'] = {
                    'engine': connection.settings_dict.get('ENGINE', 'Unknown'),
                    'name': connection.settings_dict.get('NAME', 'Unknown'),
                    'host': connection.settings_dict.get('HOST', 'Unknown'),
                }
            except Exception as e:
                context['db_error'] = str(e)
        
        return context


class PlanTypeDetailView(DetailView):
    model = PlanType
    context_object_name = "plan_type"
    template_name = "payment/plan_type_detail.html"


class CheckoutView(FormView):
    template_name = "payment/checkout.html"
    form_class = CheckoutForm
    
    def get_success_url(self):
        """Return the success URL with the plan_id parameter"""
        plan_id = self.kwargs.get('plan_id')
        return f"/payment/checkout/{plan_id}/success/"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plan_id = self.kwargs.get('plan_id')
        context['plan'] = get_object_or_404(PlanType, id=plan_id)
        return context
    
    def form_valid(self, form):
        """Handle form submission and create subscription"""
        try:
            with transaction.atomic():
                # Get the plan type
                plan_type = get_object_or_404(PlanType, id=self.kwargs.get('plan_id'))
                
                # Calculate dates
                start_date = timezone.now().date()
                end_date = start_date + timedelta(days=30)  # Default to 30 days
                
                # Create subscription record
                subscription = Subscription.objects.create(
                    academy_name=form.cleaned_data['academy_name'],
                    plan_type=plan_type,
                    price=plan_type.monthly_price,
                    duration_days=30,
                    start_date=start_date,
                    end_date=end_date,
                    payment_method=form.cleaned_data['payment_method'],
                    contact_email=form.cleaned_data['contact_email'],
                    contact_phone=form.cleaned_data.get('contact_phone', ''),
                    billing_address=form.cleaned_data['address'],
                    status=Subscription.Status.PENDING,
                    notes=f"Checkout completed on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                
                # Simulate payment processing (in real app, this would integrate with payment gateway)
                if form.cleaned_data['payment_method'] == 'card':
                    # Simulate card payment
                    if self.simulate_card_payment(form.cleaned_data):
                        subscription.status = Subscription.Status.SUCCESSFUL
                        subscription.payment_date = timezone.now()
                        subscription.transaction_id = f"TXN{subscription.id:06d}"
                        subscription.notes += f"\nPayment successful via card. Transaction ID: {subscription.transaction_id}"
                    else:
                        subscription.status = Subscription.Status.FAILED
                        subscription.error_message = "Card payment failed. Please check your card details."
                        subscription.notes += "\nCard payment failed"
                else:
                    # Bank transfer - mark as pending
                    subscription.status = Subscription.Status.PENDING
                    subscription.notes += "\nBank transfer initiated. Payment will be processed within 2-3 business days."
                
                subscription.save()
                
                # Send invoice email
                try:
                    subscription.send_invoice()
                    messages.success(self.request, "Invoice has been sent to your email address.")
                except Exception as e:
                    messages.warning(self.request, f"Invoice email failed to send: {str(e)}")
                
                # Store subscription ID in session for success page
                self.request.session['subscription_id'] = subscription.id
                
                messages.success(self.request, "Subscription created successfully!")
                
        except Exception as e:
            messages.error(self.request, f"An error occurred: {str(e)}")
            return self.form_invalid(form)
        
        return super().form_valid(form)
    
    def simulate_card_payment(self, form_data):
        """Simulate card payment processing"""
        # In a real application, this would integrate with a payment gateway
        # For now, we'll simulate a 90% success rate
        import random
        return random.random() > 0.1  # 90% success rate


class CheckoutSuccessView(DetailView):
    model = Subscription
    template_name = "payment/checkout_success.html"
    context_object_name = "subscription"
    
    def get_object(self):
        """Get subscription from session or redirect if not found"""
        subscription_id = self.request.session.get('subscription_id')
        if not subscription_id:
            messages.error(self.request, "No subscription found. Please complete checkout first.")
            # Redirect to plan types list if no subscription in session
            return None
        
        try:
            subscription = get_object_or_404(Subscription, id=subscription_id)
            return subscription
        except:
            messages.error(self.request, "Invalid subscription. Please complete checkout first.")
            return None
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object:
            context['academy'] = self.object.academy_name
            context['plan_type'] = self.object.plan_type
        return context
    
    def dispatch(self, request, *args, **kwargs):
        """Handle dispatch and redirect if no subscription found"""
        response = super().dispatch(request, *args, **kwargs)
        
        # If no subscription object, redirect to plan types
        if not self.object:
            return redirect('payment:plan_type_list')
        
        return response


class SubscriptionPlanListView(ListView):
    model = SubscriptionPlan
    context_object_name = "plans"
    template_name = "payment/plan_list.html"


class SubscriptionPlanDetailView(DetailView):
    model = SubscriptionPlan
    context_object_name = "plan"
    template_name = "payment/plan_detail.html"
