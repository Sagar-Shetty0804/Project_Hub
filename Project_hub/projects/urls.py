from django.urls import path

from . import views

app_name = "projects"

urlpatterns = [
    path("", views.explore, name="explore"),
    path("saved/", views.bookmarks, name="bookmarks"),
    path("new/", views.create, name="create"),
    path("join/", views.join, name="join"),
    path("<str:code>/", views.detail, name="detail"),
    path("<str:code>/edit/", views.edit, name="edit"),
    path("<str:code>/team/", views.team, name="team"),
    path("<str:code>/like/", views.toggle_like, name="like"),
    path("<str:code>/bookmark/", views.toggle_bookmark, name="bookmark"),
    path("<str:code>/media/", views.media_upload, name="media_upload"),
    path("<str:code>/media/<int:pk>/delete/", views.media_delete, name="media_delete"),
    path("<str:code>/links/", views.link_add, name="link_add"),
    path("<str:code>/links/<int:pk>/delete/", views.link_delete, name="link_delete"),
    path("<str:code>/vault/", views.vault_browse, name="vault"),
    path("<str:code>/vault/upload/", views.vault_upload, name="vault_upload"),
    path("<str:code>/vault/new/", views.vault_new, name="vault_new"),
    path("<str:code>/vault/<int:pk>/", views.vault_file, name="file"),
    path("<str:code>/vault/<int:pk>/raw/", views.vault_raw, name="file_raw"),
    path("<str:code>/vault/<int:pk>/edit/", views.vault_edit, name="file_edit"),
    path("<str:code>/vault/<int:pk>/delete/", views.vault_delete, name="file_delete"),
    path("<str:code>/vault/<int:pk>/restore/", views.vault_restore, name="file_restore"),
]
