from django.shortcuts import render
from django.http import HttpResponse


def base_view(request):
    return render(request, "main/base.html")
