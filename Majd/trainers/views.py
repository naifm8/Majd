from django.shortcuts import render, redirect
from django.http import HttpResponse,HttpRequest

# Create your views here.


def teain_dashboard_view(request:HttpRequest):
    return render(request, "trainers/teain_dashboard.html")