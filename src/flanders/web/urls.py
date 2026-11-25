from django.urls import include, path

urlpatterns = [path("", include("flanders.web.runs.urls"))]
