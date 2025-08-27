
from django.shortcuts import render
from django.http import HttpResponse,HttpRequest
from django.shortcuts import render, redirect
from .forms import ContactForm
from django.contrib import messages



def main_home_view(request:HttpRequest):
    return render(request, "main/main_home.html")



def contact_view(request:HttpRequest):

    
    if request.method == "POST":
        form = ContactForm(request.POST)  
        if form.is_valid():
            form.save()
            messages.success(request, "Message sent successfully.", "alert-success")
            return redirect("main:contact_view") 
        else:
            messages.error(request, "Please fix the errors below.", "alert-danger")
    else:
        form = ContactForm()

    return render(request, "main/contact_us.html", {"form": form})



def subscriptions_view(request):

    return render(request, "main/subscriptions_page.html")



def our_vision_view(request:HttpRequest):
    
    return render(request, "main/our_vision.html")


def about_view(request):
    return render(request, "main/about.html")

