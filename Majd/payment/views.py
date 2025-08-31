from django.views.generic import ListView, DetailView
from django.views.generic.edit import FormView
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from .models import PlanType, SubscriptionPlan
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
    success_url = reverse_lazy('payment:checkout_success')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plan_id = self.kwargs.get('plan_id')
        context['plan'] = get_object_or_404(PlanType, id=plan_id)
        return context
    
    def form_valid(self, form):
        # Handle form submission and payment processing here
        # For now, just redirect to success page
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
