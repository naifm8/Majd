from django.shortcuts import render
from django.http import HttpResponse
from .forms import ContactForm

def main_home_view(request):
    return render(request, "main/main_home.html")


def contact_view(request):
    form = ContactForm(request.POST)

    if request.method == "POST" and form.is_valid():
        form.save()

    return render(request, "main/contact_us.html" ,{"form": form})


