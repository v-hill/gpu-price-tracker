from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render

from .forms import GraphicsCardForm
from .models import GraphicsCard


def home(request):
    return render(request, "home.html")


def top_sales(request):
    data = GraphicsCard.objects.all()
    if request.method == "POST":
        form = GraphicsCardForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("/")
    else:
        form = GraphicsCardForm()
    context = {
        "data": data,
        "form": form,
        "nmenu": "top_sales",
    }
    return render(request, "sales_bar.html", context)


def search_chart(request):
    name_choices = GraphicsCard.objects.all()
    name_choices = {q["model"]: q["id"] for q in name_choices.values()}

    search_term = request.GET.get("search")

    if search_term:
        data = GraphicsCard.objects.filter(model__icontains=search_term)
    else:
        data = GraphicsCard.objects.all()
        search_term = "Select a model"

    context = {
        "data": data,
        "name_choices": name_choices,
        "search_term": str(search_term),
        "nmenu": "search_chart",
    }

    return render(request, "search_chart.html", context)
