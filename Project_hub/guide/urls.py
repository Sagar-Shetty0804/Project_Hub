from django.urls import path
from guide import views

urlpatterns = [
    path('',views.groups,name='start'),
    path('groups/',views.groups,name='groups'),
    path('addGroup/',views.addGroup,name='addGroup'),
    path('studentView/',views.studentView,name='studentView'),
    path('view_file_content_guide/<str:file_type>/<int:file_id>/', views.view_file_content_guide, name='view_file_content_guide'),
    path('table/',views.table,name='table'),
]
