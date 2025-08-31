from django.urls import path
from . import views

app_name = "player_payments"

urlpatterns = [
    # Subscription listing and details
    path('', views.PlayerSubscriptionListView.as_view(), name='subscription_list'),
    path('subscription/<int:pk>/', views.PlayerSubscriptionDetailView.as_view(), name='subscription_detail'),
    path('academy/<int:academy_id>/subscriptions/', views.academy_subscriptions_view, name='academy_subscriptions'),
    
    # Enrollment process
    path('enroll/<int:pk>/child/<int:child_id>/', views.EnrollmentView.as_view(), name='enroll'),
    path('enrollment/<int:pk>/', views.EnrollmentDetailView.as_view(), name='enrollment_detail'),
    path('my-enrollments/', views.my_enrollments_view, name='my_enrollments'),
    
    # Payment completion
    path('payment/<int:enrollment_id>/complete/', views.complete_payment_view, name='complete_payment'),
]
