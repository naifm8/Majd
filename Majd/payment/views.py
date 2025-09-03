from django.views.generic import ListView, DetailView
from django.views.generic.edit import FormView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from .models import PlanType, SubscriptionPlan, Subscription
from .forms import CheckoutForm
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages


class PlanTypeListView(ListView):
    model = PlanType
    context_object_name = "plan_types"
    template_name = "payment/plan_type_list.html"
    queryset = PlanType.objects.all().order_by('display_order')

class PlanTypeDetailView(DetailView):
    model = PlanType
    context_object_name = "plan_type"
    template_name = "payment/plan_type_detail.html"

class CheckoutView(FormView):
    template_name = "payment/checkout.html"
    form_class = CheckoutForm
    
    def get_success_url(self):
        plan_id = self.kwargs.get('plan_id')
        return reverse_lazy('payment:checkout_success', kwargs={'plan_id': plan_id})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plan_id = self.kwargs.get('plan_id')
        context['plan'] = get_object_or_404(PlanType, id=plan_id)
        return context
    
    def form_valid(self, form):
        # Handle form submission and payment processing
        plan_id = self.kwargs.get('plan_id')
        plan_type = get_object_or_404(PlanType, id=plan_id)
        
        # Create subscription record
        from django.utils import timezone
        from datetime import timedelta
        
        subscription = Subscription.objects.create(
            academy_name=form.cleaned_data['academy_name'],
            plan_type=plan_type,
            price=plan_type.monthly_price,
            duration_days=30,  # Default to monthly
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=30)).date(),
            payment_method=form.cleaned_data['payment_method'],
            contact_email=form.cleaned_data['contact_email'],
            contact_phone=form.cleaned_data['contact_phone'],
            billing_address=form.cleaned_data['address'],
            status=Subscription.Status.PENDING,  # Start as pending
        )
        
        # For demo purposes, mark as successful immediately
        # In production, this would happen after payment gateway confirmation
        subscription.status = Subscription.Status.SUCCESSFUL
        subscription.payment_date = timezone.now()
        subscription.transaction_id = f"DEMO_{subscription.id}"
        subscription.save()
        
        # Send invoice email
        subscription.send_invoice()
        
        return super().form_valid(form)

class CheckoutSuccessView(DetailView):
    model = PlanType
    template_name = "payment/checkout_success.html"
    context_object_name = "plan"
    
    def get_object(self):
        plan_id = self.kwargs.get('plan_id')
        return get_object_or_404(PlanType, id=plan_id)

class SubscriptionPlanListView(ListView):
    model = SubscriptionPlan
    context_object_name = "plans"
    template_name = "payment/plan_list.html"

class SubscriptionPlanDetailView(DetailView):
    model = SubscriptionPlan
    context_object_name = "plan"
    template_name = "payment/plan_detail.html"


# ✅ Plan Type Get Started Redirect
def plan_type_get_started_redirect(request, plan_id):
    """
    Redirect users based on their authentication status and profile type:
    - If authenticated academy admin: redirect to checkout
    - If not authenticated or not academy admin: redirect to get started page
    """
    if request.user.is_authenticated:
        # Check if user has an academy admin profile
        if hasattr(request.user, 'academy_admin_profile'):
            # Redirect to checkout for this plan
            return redirect('payment:checkout', plan_id=plan_id)
        else:
            # User is authenticated but not an academy admin, redirect to get started
            return redirect('accounts:selection_view')
    else:
        # Not authenticated, redirect to get started
        return redirect('accounts:selection_view')


@login_required
def subscription_step(request):
    plans = PlanType.objects.all().order_by("display_order")

    if request.method == "POST":
        plan_id = request.POST.get("plan_id")
        plan = get_object_or_404(PlanType, id=plan_id)

        # Create a subscription (fake success for now)
        Subscription.objects.create(
            academy_name=request.user.username,
            plan_type=plan,
            price=plan.monthly_price,
            duration_days=30,  # could extend per plan logic
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timezone.timedelta(days=30),
            contact_email=request.user.email,
            status="successful",
        )

        messages.success(request, f"You subscribed to {plan.name} ✅")
        return redirect("academies:setup")

    return render(request, "payment/subscription_step.html", {"plans": plans})

