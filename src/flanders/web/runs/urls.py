from django.urls import path

from flanders.web.runs import views

app_name = "runs"
urlpatterns = [
    path("", views.home, name="home"),
    path("runs/", views.run_list, name="list"),
    path("runs/<str:run_id>/", views.genomes, name="genomes"),
    path("runs/<str:run_id>/genomes/<str:tag>/", views.genome, name="genome"),
    path("runs/<str:run_id>/genomes/<str:tag>/<str:location>/provenance/", views.provenance, name="provenance"),
    path("runs/<str:run_id>/config.yaml", views.export_config, name="export_config"),
    path("runs/<str:run_id>/ledger/", views.ledger, name="ledger"),
    path("runs/<str:run_id>/cancel/", views.cancel, name="cancel"),
    path("runs/<str:run_id>/resume/", views.resume, name="resume"),
    path("ledger/", views.ledger, name="ledger_active"),
    path("compose/", views.compose, name="compose"),
    path("citation/", views.citation, name="citation"),
]
