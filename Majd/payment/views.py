from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView, DetailView, FormView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta

from .models import PlanType, SubscriptionPlan, Subscription
from .forms import CheckoutForm


class PlanTypeDetailView(DetailView):
    model = PlanType
    context_object_name = "plan_type"
    template_name = "payment/plan_type_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["step"] = 1  # Step 1: choose plan
        return context


class PlanTypeListView(ListView):
    model = PlanType
    context_object_name = "plan_types"
    template_name = "payment/plan_type_list.html"
    queryset = PlanType.objects.all().order_by("display_order")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["step"] = 1  # Step 1: choose plan
        return context


class CheckoutView(FormView):
    template_name = "payment/checkout.html"
    form_class = CheckoutForm

    def get_success_url(self):
        plan_id = self.kwargs.get("plan_id")
        return reverse_lazy("payment:checkout_success", kwargs={"plan_id": plan_id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plan_id = self.kwargs.get("plan_id")
        context["plan"] = get_object_or_404(PlanType, id=plan_id)
        context["step"] = 2  # Step 2: checkout
        return context

    def form_valid(self, form):
        plan_id = self.kwargs.get("plan_id")
        plan_type = get_object_or_404(PlanType, id=plan_id)

        # Create subscription record
        subscription = Subscription.objects.create(
            academy_name=form.cleaned_data["academy_name"],
            plan_type=plan_type,
            price=plan_type.monthly_price,
            duration_days=30,  # Default monthly
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=30)).date(),
            payment_method=form.cleaned_data["payment_method"],
            contact_email=form.cleaned_data["contact_email"],
            contact_phone=form.cleaned_data["contact_phone"],
            billing_address=form.cleaned_data["address"],
            status=Subscription.Status.PENDING,
        )

        # Demo: mark immediately successful
        subscription.status = Subscription.Status.SUCCESSFUL
        subscription.payment_date = timezone.now()
        subscription.transaction_id = f"DEMO_{subscription.id}"
        subscription.save()

        subscription.send_invoice()
        return super().form_valid(form)


class CheckoutSuccessView(DetailView):
    model = PlanType
    template_name = "payment/checkout_success.html"
    context_object_name = "plan"

    def get_object(self):
        plan_id = self.kwargs.get("plan_id")
        return get_object_or_404(PlanType, id=plan_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["step"] = 3  # Step 3: success
        return context


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
    if request.user.is_authenticated:
        if hasattr(request.user, "academy_admin_profile"):
            return redirect("payment:checkout", plan_id=plan_id)
        else:
            return redirect("accounts:selection_view")
    else:
        return redirect("accounts:selection_view")


@login_required
def subscription_step(request):
    plans = PlanType.objects.all().order_by("display_order")

    if request.method == "POST":
        plan_id = request.POST.get("plan_id")
        plan = get_object_or_404(PlanType, id=plan_id)

        # 👇 Instead of creating subscription directly, go to checkout
        return redirect("payment:checkout", plan_id=plan.id)

    return render(
        request,
        "payment/subscription_step.html",
        {"plans": plans, "step": 1},  # subscription step = choose plan
    )



