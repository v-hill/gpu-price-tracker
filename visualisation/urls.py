from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("total_sales/", views.total_sales, name="total_sales"),
    path(
        "total_sales_filtered/",
        views.total_sales_filtered,
        name="total_sales_filtered",
    ),
    path(
        "individual_scatter/",
        views.individual_scatter,
        name="individual_scatter",
    ),
]
