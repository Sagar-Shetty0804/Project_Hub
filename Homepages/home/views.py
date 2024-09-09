from django.shortcuts import render, HttpResponse

# Create your views here.
def groups(request):
    return render(request, 'home.html')


def search(request):
    return render(request,'search.html')

def upload(request):
    return render(request,'upload.html')

def resources(request):
    return render(request,'resources.html')