from django.shortcuts import render, redirect
from django.http import HttpResponse,HttpRequest

# Create your views here.


def overview_view(request:HttpRequest):
    return render(request, "trainers/overview.html")