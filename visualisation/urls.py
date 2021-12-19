from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("search_chart/", views.search_chart, name="search_chart"),
    path("top_sales/", views.top_sales, name="top_sales"),
]
