from django.contrib import admin
from django.urls import path,include
from student import views
from django.conf import settings
from django.conf.urls.static import static


app_name = 'student' 

urlpatterns = [
    path('',views.search,name='search'), #search page is replace with the homepage 
    
    path('search/',views.search,name = 'Search'),
    path('resources/',views.resources,name = 'Resources'),
    
    path('homepage/file/',views.group_file,name = 'File'),
    path('homepage/groups/',views.group_groups,name = 'Groups'),
    path('upload/document/', views.upload_document_file, name='upload_document_file'),
    path('upload/additional/', views.upload_additional_file, name='upload_additional_file'),
    path('upload/database/', views.database, name='database'),
    path('upload/', views.upload_code_file, name='upload_code_file'),
    path('files/', views.file_list, name='file_list'),  # New URL pattern for the file list
    path('files/<str:file_type>/<int:file_id>/', views.view_file_content, name='view_file_content'),  # New URL pattern
    path('edit/<str:file_type>/<int:file_id>/', views.edit_file, name='edit_file'),
    path('delete/<str:file_type>/<int:file_id>/', views.delete_file, name='delete_file'),
    path('files/<str:group_code>/', views.project_link, name='file_list'),
    path('settings/', views.setting, name='settings'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

