
from django.contrib import messages
# from student.models import UploadedFile
from Login_page.models import RegisterStudent
from django.contrib.auth.models import User,Group
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .forms import CodeFileUploadForm, DatabaseFileUploadForm, DocumentFileUploadForm, AdditionalFileUploadForm
from .models import CodeFile, DatabaseFile, DocumentFile, AdditionalFile

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



# views.py

@login_required
def upload_code_file(request):
    current_user = request.user
    
    register_student = RegisterStudent.objects.get(username=current_user)
    #print(groupCode)
    print(register_student.groupCode)
    if request.method == 'POST':
        form = CodeFileUploadForm(request.POST, request.FILES)

        if form.is_valid():
            code_file = form.save(commit=False)
            code_file.group_code = register_student
            code_file.save()
    else:
        form = CodeFileUploadForm()
    return render(request, 'uploads\\upload_file.html', {'form': form, 'file_type': 'Code'})


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
    
    return render(request, 'uploads\\file_list.html', context)


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

    return render(request, 'uploads\\view_file_content.html', {'file': file_obj, 'file_type': file_type})


@login_required
def edit_file(request, file_type, file_id):
    # Determine the type of file and get the corresponding file object
    if file_type == 'code':
        file_obj = get_object_or_404(CodeFile, id=file_id)
    else:
        return render(request, '404.html')
    if request.method == 'POST':
        file_obj.content = request.POST.get('content', '')
        file_obj.save(update_fields=['content'])
        messages.success(request, "File content updated successfully!")
        return redirect('student:file_list')

    return render(request, 'uploads\\edit_file_content.html', {'file': file_obj})
    
@login_required
def delete_file(request, file_type, file_id):
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

    if request.method == 'POST':
        file_obj.delete()
        messages.success(request, "File deleted successfully!")
        return redirect('student:file_list')  # Redirect to the list view after deletion

    return render(request, 'uploads\\delete_file.html', {'file': file_obj})


@login_required
def database(request):
    current_user = request.user
    print(current_user)
    register_student = RegisterStudent.objects.get(username=current_user)
    #print(groupCode)
    if request.method == 'POST':
        form = DatabaseFileUploadForm(request.POST, request.FILES)

        if form.is_valid():
            database_file = form.save(commit=False)
            database_file.group_code = register_student
            database_file.save()
    else:
        form = DatabaseFileUploadForm()
    return render(request, 'uploads\\database.html', {'form': form, 'file_type': 'Database'})

@login_required
def upload_document_file(request):
    current_user = request.user
    print(current_user)
    register_student = RegisterStudent.objects.get(username=current_user)
    if request.method == 'POST':
        form = DocumentFileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            code_file = form.save(commit=False)
            code_file.group_code = register_student
            code_file.save()  # Save the document file without processing content  
    else:
        form = DocumentFileUploadForm()
    
    return render(request, 'uploads\\document.html', {'form': form})

@login_required
def upload_additional_file(request):
    current_user = request.user
    print(current_user)
    register_student = RegisterStudent.objects.get(username=current_user)
    if request.method == 'POST':
        form = AdditionalFileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            code_file = form.save(commit=False)
            code_file.group_code = register_student
            code_file.save()  # Save the additional file without processing content
            return redirect('student:file_list')  # Redirect to file list after upload
    else:
        form = AdditionalFileUploadForm()
    
    return render(request, 'uploads\\additional.html', {'form': form})