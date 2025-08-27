from django.urls import path
from . import views

app_name = "parents"


urlpatterns = [
    path('dashboard/overview/', views.dashboard_view, name='dashboard_view'),
    path('dashboard/children/', views.my_children_view, name='my_children_view'),
    path('dashboard/add/child/', views.add_child_view, name='add_child_view'),
    path('dashboard/edit/child/<int:child_id>/', views.edit_child_view, name='edit_child_view'),
    path('children/delete/<int:child_id>/', views.delete_child_view, name='delete_child_view'),
    path('schedule/', views.schedule_view, name='schedule_view'),
    path('payments/', views.payments_view, name='payments_view'),

]
