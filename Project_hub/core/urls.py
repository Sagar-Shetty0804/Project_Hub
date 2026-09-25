from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.landing, name="landing"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("insights/", views.insights, name="insights"),
    path("pdf/<str:code>/report/", views.report, name="report"),
    path("pdf/<str:code>/certificate/<int:user_id>/", views.certificate, name="certificate"),
]
