from django.urls import path

from . import views

app_name = "evaluation"

urlpatterns = [
    path("", views.index, name="index"),
    path("rubrics/new/", views.rubric_edit, name="rubric_new"),
    path("rubrics/<int:pk>/", views.rubric_edit, name="rubric_edit"),
    path("rounds/new/", views.round_create, name="round_new"),
    path("rounds/<int:pk>/", views.round_detail, name="round"),
    path("rounds/<int:pk>/export/", views.export, name="export"),
    path("rounds/<int:pk>/mark/<str:code>/", views.mark, name="mark"),
    path("feature/<str:code>/", views.toggle_featured, name="feature"),
]
