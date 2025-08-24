from django.shortcuts import render
from django.http import HttpResponse,HttpRequest


def main_home_view(request:HttpRequest):
    return render(request, "main/main_home.html")


def contact_view(request:HttpRequest):
    
    return render(request, "main/contact_us.html")


def our_vision_view(request:HttpRequest):
    
    return render(request, "main/our_vision.html")