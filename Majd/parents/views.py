from django.shortcuts import render, redirect
from django.http import HttpResponse,HttpRequest
from .models import Child
# Create your views here.

def dashboard_view(request):
    children = []

    if request.user.is_authenticated and hasattr(request.user, "parent_profile"):
        children = Child.objects.filter(parent=request.user.parent_profile).with_age()

    return render(request, "main/overview.html", {'children':children, "children_count": children.count(),})


def my_children_view(request):
    children = []
    if request.user.is_authenticated and hasattr(request.user, "parent_profile"):
        children = Child.objects.filter(parent=request.user.parent_profile).with_age()

    
    return render(request, "main/my_children.html", {"children": children,})