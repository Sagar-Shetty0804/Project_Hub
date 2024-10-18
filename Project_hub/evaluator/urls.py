from django.urls import path
from evaluator import views

urlpatterns = [
    path('',views.studentGroups,name='studentGroups'),
    path('studentGroup/',views.studentGroups,name='studentGroups'),
    path('studentView/',views.studentView,name='studentView'),
    path('table/',views.table,name='table'),
    path('files/<str:file_type>/<int:file_id>/', views.view_file_content_eval, name='view_file_content_eval'),
    
]