from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import File, Folder
from .forms import FileUploadForm, FolderForm, FileEditForm

@login_required
def home(request):
    folders = Folder.objects.all()
    files = File.objects.all()  
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file_name = form.cleaned_data['name']
            uploaded_file = request.FILES['file']
            file_content = uploaded_file.read().decode('utf-8')  
            file_instance = File(name=file_name, content=file_content, user=request.user)
            file_instance.save()
            return redirect('home')
    else:
        form = FileUploadForm()
    return render(request, 'home.html', {'folders':folders,'files': files, 'form': form})


    

@login_required
def create_folder(request):
    if request.method == 'POST':
        form = FolderForm(request.POST)
        if form.is_valid():
            folder = form.save(commit=False)
            folder.user = request.user
            folder.save()
            return redirect('home')
    else:
        form = FolderForm()
    return render(request, 'create_folder.html', {'form': form})

@login_required
def upload_file(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            file = form.save(commit=False)
            file.user = request.user
            file.save()
            return redirect('home')
    else:
        form = FileUploadForm(user=request.user)
    return render(request, 'upload_file.html', {'form': form})


def view_folder(request, folder_id):
    folder = get_object_or_404(Folder, id=folder_id)
    files = folder.files.all()  # Get all files in this folder
    return render(request, 'view_folder.html', {'folder': folder, 'files': files})

@login_required
def edit_file(request, file_id):
    file = get_object_or_404(File, id=file_id, user=request.user)
    if request.method == 'POST':
        form = FileEditForm(request.POST, instance=file)
        if form.is_valid():
            form.save()
            return redirect('display_file_content', file_id=file.id)
    else:
        form = FileEditForm(instance=file)
    return render(request, 'edit_file.html', {'form': form, 'file_name': file.name})


def display_file_content(request, file_id):
    file = get_object_or_404(File, id=file_id)
    is_owner = file.user == request.user
    return render(request, 'display_file.html', {
        'file_content': file.content,
        'file_name': file.name,
        'file_id': file.id,
        'is_owner': is_owner,
    })

# fileviewer/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful.")
            return redirect('home')
        messages.error(request, "Registration failed. Please try again.")
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'login.html')

@login_required
def user_logout(request):
    logout(request)
    return redirect('login')
