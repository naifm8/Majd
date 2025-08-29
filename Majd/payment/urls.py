from django.urls import path
from . import views

app_name = "payment"

urlpatterns = [
    path("plan-types/", views.PlanTypeListView.as_view(), name="plan_type_list"),
    path("plan-types/<int:pk>/", views.PlanTypeDetailView.as_view(), name="plan_type_detail"),
    path("checkout/<int:plan_id>/", views.CheckoutView.as_view(), name="checkout"),
    path("checkout/<int:plan_id>/success/", views.CheckoutSuccessView.as_view(), name="checkout_success"),
    path("plans/", views.SubscriptionPlanListView.as_view(), name="plan_list"),
    path("plans/<int:pk>/", views.SubscriptionPlanDetailView.as_view(), name="plan_detail"),
]
