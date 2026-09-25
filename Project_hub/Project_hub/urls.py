from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "ProjectHub Admin"
admin.site.site_title = "ProjectHub Admin"
admin.site.index_title = "Manage ProjectHub"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("accounts/", include("accounts.urls")),
    path("projects/", include("projects.urls")),
    path("mentoring/", include("mentoring.urls")),
    path("evaluation/", include("evaluation.urls")),
    path("notifications/", include("notifications.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
