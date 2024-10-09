from django.contrib import admin
from django.urls import path,include
from student import views
from django.conf import settings
from django.conf.urls.static import static


app_name = 'student' 

urlpatterns = [
    path('',views.homePage,name='Homepage'),
    
    path('search/',views.search,name = 'Search'),
    path('resources/',views.resources,name = 'Resources'),
    
    path('homepage/file/',views.group_file,name = 'File'),
    path('homepage/groups/',views.group_groups,name = 'Groups'),
    
    path('upload/',views.upload_code_file,name = 'upload_code_file'),
    path('upload/document/', views.document_view, name='document'),
    path('upload/additional/', views.additional_view, name='additional'),
    path('upload/database/', views.database_view, name='database'),
    path('upload/code/', views.upload_code_file, name='upload_code_file'),
    path('files/', views.file_list, name='file_list'),  # New URL pattern for the file list
    path('files/<str:file_type>/<int:file_id>/', views.view_file_content, name='view_file_content'),  # New URL pattern
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)