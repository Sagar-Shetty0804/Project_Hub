from django.shortcuts import render,HttpResponse

# Create your views here.
def home(request):
    return render(request,"home.html")

def rockPaperScissors(request):
    return render(request,"rockPaperScissors.html")

def ticTakToe(request):
    return render(request,"ticTakToe.html")