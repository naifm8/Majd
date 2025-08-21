from django.shortcuts import render
from django.http import HttpResponse


def main_home_view(request):
    return render(request, "main/main_home.html")
