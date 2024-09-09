from django.contrib import admin
from django.urls import path
from home import views

urlpatterns = [
    path("", views.groups, name='home'),
    path("groups", views.groups, name='groups'),
    path("search", views.search, name='search'),
    path("upload", views.upload, name='upload'),
    path("resources", views.resources, name='resources'),


]