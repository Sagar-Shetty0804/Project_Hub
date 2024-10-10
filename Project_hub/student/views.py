from django.shortcuts import render,redirect
from django.contrib import messages
# from student.models import UploadedFile
from Login_page.models import RegisterStudent
from django.contrib.auth.models import User,Group
from django.contrib.auth.decorators import login_required
# Create your views here.
def homePage(request):
    print("working")
    return render(request,'student\\home.html')

def search(request):
    return render(request,'student\\search.html')

def resources(request):
    return render(request,'student\\resources.html')

def group_file(request):
    return render(request,'group\\file.html')

def group_groups(request):
    return render(request,'group\\groups.html')

def code(request):
    return render(request, 'uploads\\code.html')

# Folder View Page
def document_view(request):
    return render(request, 'uploads\\document.html')

# Additional View Page
def additional_view(request):
    return render(request, 'uploads\\additional.html')

# Database View Page
def database_view(request):
    return render(request, 'uploads\\database.html')

#View Details Page
def view_details(request):
    return render(request, 'uploads\\view.html')

# views.py
from django.shortcuts import render, redirect, get_object_or_404
from .forms import CodeFileUploadForm, DatabaseFileUploadForm, DocumentFileUploadForm, AdditionalFileUploadForm
from .models import CodeFile, DatabaseFile, DocumentFile, AdditionalFile

@login_required
def upload_code_file(request):
    current_user = request.user
    print(current_user)
    register_student = RegisterStudent.objects.get(username=current_user)
    #print(groupCode)
    if request.method == 'POST':
        form = CodeFileUploadForm(request.POST, request.FILES)

        if form.is_valid():
            code_file = form.save(commit=False)
            code_file.group_code = register_student
            code_file.save()
    else:
        form = CodeFileUploadForm()
    return render(request, 'uploa\\upload_file.html', {'form': form, 'file_type': 'Code'})


@login_required
def file_list(request):
    current_user = request.user
    try:
        register_student = RegisterStudent.objects.get(username=current_user)
    except RegisterStudent.DoesNotExist:
        messages.error(request, "You do not have a group code associated with your account.")
        return redirect('home')
    code_files = CodeFile.objects.filter(group_code=register_student)
    database_files = DatabaseFile.objects.all()
    document_files = DocumentFile.objects.all()
    additional_files = AdditionalFile.objects.all()

    context = {
        'code_files': code_files,
        'database_files': database_files,
        'document_files': document_files,
        'additional_files': additional_files,
    }
    
    return render(request, 'uploa\\file_list.html', context)


def view_file_content(request, file_type, file_id):
    # Determine the type of file and get the corresponding file object
    if file_type == 'code':
        file_obj = get_object_or_404(CodeFile, id=file_id)
    elif file_type == 'database':
        file_obj = get_object_or_404(DatabaseFile, id=file_id)
    elif file_type == 'document':
        file_obj = get_object_or_404(DocumentFile, id=file_id)
    elif file_type == 'additional':
        file_obj = get_object_or_404(AdditionalFile, id=file_id)
    else:
        return render(request, '404.html')  # Handle unknown file types

    return render(request, 'uploa\\view_file_content.html', {'file': file_obj, 'file_type': file_type})
