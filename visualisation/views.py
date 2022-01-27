import datetime
import json

import pytz
from django.shortcuts import render

from scraper.models import EbayGraphicsCard
from visualisation.models import GraphicsCard, Sale

EPOCH = pytz.utc.localize(datetime.datetime.utcfromtimestamp(0))


def unix_time_millis(dt):
    return (dt - EPOCH).total_seconds() * 1000.0


def home(request):
    return render(request, "home.html")


def total_sales(request):
    data = EbayGraphicsCard.objects.all().order_by("-total_collected")[:20]
    context = {
        "data": data,
        "nmenu": "total_sales",
    }
    return render(request, "total_sales.html", context)


def individual_scatter(request):
    model_choices = GraphicsCard.objects.all()
    model_choices = {q["model"]: q["id"] for q in model_choices.values()}

    search_term = request.GET.get("search")

    if search_term:
        gpu = GraphicsCard.objects.filter(model__icontains=search_term).first()
    else:
        gpu = GraphicsCard.objects.all().first()
        search_term = "Select a model"

    data = Sale.objects.filter(gpu__id=gpu.id)
    data = list(data.values_list("date", "total_price"))
    plot_data = [
        {"x": unix_time_millis(point[0]), "y": point[1]} for point in data
    ]
    max_price = max([point[1] for point in data])

    context = {
        "plot_data": json.dumps(plot_data),
        "max_price": max_price,
        "model_choices": model_choices,
        "search_term": str(search_term),
        "nmenu": "individual_scatter",
    }

    return render(request, "individual_scatter.html", context)
