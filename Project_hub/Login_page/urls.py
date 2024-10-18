from django.contrib import admin
from django.urls import path
from Login_page import views

urlpatterns = [
    path("",views.studentLogin,name="studentLogin"),
    path("studentLogin/",views.studentLogin,name="studentLogin"),
    path('registerStudent/',views.registerStudent,name="register Student"),
    path('guideLogin/',views.guideLogin,name='guideLogin'),
    path('evaluatorLogin/',views.evaluatorLogin,name='evaluatorLogin'),
    path('addProjectName/',views.addProjectName,name="addProjectName")
    
]