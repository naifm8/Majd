from django.urls import path
from . import views

app_name = "payment"

urlpatterns = [
    path("plan-types/", views.PlanTypeListView.as_view(), name="plan_type_list"),
    path("plan-types/<int:pk>/", views.PlanTypeDetailView.as_view(), name="plan_type_detail"),
    path("plan-types/<int:plan_id>/get-started/", views.plan_type_get_started_redirect, name="plan_type_get_started"),
    path("checkout/<int:plan_id>/", views.CheckoutView.as_view(), name="checkout"),
    path("checkout/<int:plan_id>/success/", views.CheckoutSuccessView.as_view(), name="checkout_success"),
    path("plans/", views.SubscriptionPlanListView.as_view(), name="plan_list"),
    path("plans/<int:pk>/", views.SubscriptionPlanDetailView.as_view(), name="plan_detail"),

    # Academy Subscription
    path("subscribe/", views.subscription_step, name="subscription_step"),
]
