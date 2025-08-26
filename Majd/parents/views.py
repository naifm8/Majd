from django.shortcuts import render, redirect
from django.http import HttpResponse,HttpRequest

# Create your views here.
def dashboard_view(request):

    return render(request, "main/overview.html")

