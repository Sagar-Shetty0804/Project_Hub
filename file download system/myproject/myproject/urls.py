"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from fileviewer import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('display/<int:file_id>/', views.display_file_content, name='display_file_content'),
    path('edit/<int:file_id>/', views.edit_file, name='edit_file'),
    path('folder/create/', views.create_folder, name='create_folder'),
    path('file/upload/', views.upload_file, name='upload_file'),
    path('folder/<int:folder_id>/', views.view_folder, name='view_folder'),
    path('file/view/<int:file_id>/', views.display_file_content, name='display_file_content'),
    path('file/edit/<int:file_id>/', views.edit_file, name='edit_file'),
]

