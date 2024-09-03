from django.contrib import admin
from django.urls import path
from home import views

urlpatterns = [
    path("",views.home,name='home'),
    path("rockPaperScissors/",views.rockPaperScissors,name='rockPaperScissors'),
    path("ticTakToe/",views.ticTakToe,name='ticTakToe')
]
