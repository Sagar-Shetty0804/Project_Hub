from django.urls import path

from . import views

app_name = "mentoring"

urlpatterns = [
    path("find/", views.find_groups, name="find"),
    path("adopt/", views.adopt, name="adopt"),
    path("<str:code>/", views.workspace, name="workspace"),
    path("<str:code>/release/", views.release, name="release"),
]
