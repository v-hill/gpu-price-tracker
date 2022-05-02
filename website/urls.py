"""The main definition of the URL mapping."""
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path

admin.site.site_header = (  # default: "Django Administration"
    "GPU Data Administration"
)


urlpatterns = [
    path("", include("visualisation.urls")),
    path("admin/", admin.site.urls),
]

urlpatterns += staticfiles_urlpatterns()
