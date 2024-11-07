from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from django.http import FileResponse  
from django.conf import settings  
from Login_page.models import RegisterStudent
from django.contrib.auth.models import User,Group
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .forms import CodeFileUploadForm, DatabaseFileUploadForm, DocumentFileUploadForm, AdditionalFileUploadForm
from .models import CodeFile, DatabaseFile, DocumentFile, AdditionalFile,reference
import os
# Create your views here.
def homePage(request):
    print("working")
    return render(request,'student\\home.html')

def search(request):
    # Get all projects initially
    project_queryset = RegisterStudent.objects.all()

    # Check if the request method is POST (i.e., filters are applied)
    if request.method == 'POST':
        projYear = request.POST.get('projYear')
        branch = request.POST.get('branch')
        year = request.POST.get('year')
        groupNumber = request.POST.get('groupNumber')

        # Apply filters only if they are provided
        if projYear and projYear != "":
            project_queryset = project_queryset.filter(groupCode__startswith=projYear)

        if branch and branch != "":
            project_queryset = project_queryset.filter(groupCode__icontains=f"_{branch}_")

        if year and year != "":
            project_queryset = project_queryset.filter(groupCode__icontains=f"_{year}_")

        if groupNumber and groupNumber != "":
            project_queryset = project_queryset.filter(groupCode__endswith=f"_{groupNumber}")

    # Remove duplicates using distinct group codes
    distinct_groups = project_queryset.values('groupCode').distinct()

    group_details = []
    for group in distinct_groups:
        # Fetch all students in the current group
        students_in_group = RegisterStudent.objects.filter(groupCode=group['groupCode'])
        team_members = [student.name for student in students_in_group]
        project_name = students_in_group.first().projectName if students_in_group.exists() else "Unknown"

        # Append group code, team members, and a link (assuming each group has a dedicated project page)
        group_details.append({
            'group_code': group['groupCode'],
            'project_name': project_name,
            'team_members': team_members,
            'project_link': f'/projects/{group["groupCode"]}'  # Dynamic link to the project page
        })

    context = {
        'group_details': group_details,
    }
    return render(request, 'student/search.html', context)

def resources(request):
    if request.method == 'POST':
        user  = request.user
        link = request.POST.get('refLink')
        linkName = request.POST.get('linkName')
        
        if link:
            projCode = RegisterStudent.objects.filter(username=user).values('groupCode')
            if len(projCode) != 0:
                projCode = projCode[0]['groupCode']
                register = reference(group_code=projCode,reference=link,linkName=linkName)
                register.save()
            else:
                messages.error(request, "You do not have a group code associated with your account.")
    
    user = request.user
    if user.is_authenticated:
        projCode = RegisterStudent.objects.filter(username=user).values('groupCode')[0]['groupCode']
        links = reference.objects.filter(group_code=projCode).values('reference', 'linkName')
        print(links)

            
        

    return render(request,'student\\resources.html',{'links':links})

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
    database_files = DatabaseFile.objects.filter(group_code=register_student)
    document_files = DocumentFile.objects.filter(group_code=register_student)
    additional_files = AdditionalFile.objects.filter(group_code=register_student)

    context = {
        'register_student': register_student,
        'code_files': code_files,
        'database_files': database_files,
        'document_files': document_files,
        'additional_files': additional_files,
    }
    
    return render(request, 'uploads\\file_list.html', context)

@login_required
def project_link(request, group_code):
    try:
        register_student = RegisterStudent.objects.filter(groupCode=group_code)
        if not register_student.exists():
          messages.error(request, "No group found with the provided group code.")
          return redirect('home')

        code_files = CodeFile.objects.filter(group_code__groupCode=group_code)
        database_files = DatabaseFile.objects.filter(group_code__groupCode=group_code)
        document_files = DocumentFile.objects.filter(group_code__groupCode=group_code)
        additional_files = AdditionalFile.objects.filter(group_code__groupCode=group_code)

        context = {
        'register_students': register_student,
        'code_files': code_files,
        'database_files': database_files,
        'document_files': document_files,
        'additional_files': additional_files,
        }
        return render(request, 'uploads/project.html', context)
    except RegisterStudent.DoesNotExist:
        messages.error(request, "No group found with the provided group code.")
        return redirect('home')


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

def view_file_content(request, file_type, file_id):
    # Determine the type of file and get the corresponding file object
    if file_type == 'code':
        file_obj = get_object_or_404(CodeFile, id=file_id)
    elif file_type == 'database':
        file_obj = get_object_or_404(DatabaseFile, id=file_id)
    elif file_type == 'document':
        file_obj = get_object_or_404(DocumentFile, id=file_id)
        if file_obj.file.name.endswith('.pdf'):
            file_path = os.path.join(settings.MEDIA_ROOT, file_obj.file.name)
            return FileResponse(open(file_path, 'rb'), content_type='application/pdf')
    elif file_type == 'additional':
        file_obj = get_object_or_404(AdditionalFile, id=file_id)
    else:
        return render(request, '404.html')  # Handle unknown file types

    return render(request, 'uploads\\view_file_content.html', {'file': file_obj, 'file_type': file_type})

def project_file_content(request, file_type, file_id):
    # Determine the type of file and get the corresponding file object
    if file_type == 'code':
        file_obj = get_object_or_404(CodeFile, id=file_id)
    elif file_type == 'database':
        file_obj = get_object_or_404(DatabaseFile, id=file_id)
    elif file_type == 'document':
        file_obj = get_object_or_404(DocumentFile, id=file_id)
        if file_obj.file.name.endswith('.pdf'):
            file_path = os.path.join(settings.MEDIA_ROOT, file_obj.file.name)
            return FileResponse(open(file_path, 'rb'), content_type='application/pdf')
    elif file_type == 'additional':
        file_obj = get_object_or_404(AdditionalFile, id=file_id)
    else:
        return render(request, '404.html')  # Handle unknown file types

    return render(request, 'uploads\\projectview.html', {'file': file_obj, 'file_type': file_type})

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

def setting(request):
    

    
    if request.method == 'POST':
        
        if 'update' in request.POST:
            print("update")
            
            currentPassword = request.POST.get('currentPassword')
            confirmPassword = request.POST.get('confirmPassword')
            newPassword = request.POST.get('newPassword')
            
            if currentPassword :
                # Perform password validation and update logic
                user = request.user
                if user.check_password(currentPassword):
                    if confirmPassword == newPassword :
                        # user.set_password(newPassword)
                        # user.save()
                        if len(newPassword) >= 8:
                            user.set_password(newPassword)
                            user.save()
                        
                            messages.success(request, 'Password updated successfully.')
                        else:
                            messages.warning(request, 'Password must be at least 8 characters long.')
                    else:
                        messages.warning(request, 'Passwords do not match.')
                else:
                    messages.warning(request, 'Incorrect current password.')
            else:
                messages.warning(request, 'Please enter your current password.')        
        
        elif 'logout' in request.POST:
            # Handle logout logic
            logout(request)
            messages.success(request, 'Logged out successfully.')
            return redirect('/')
        elif 'delete' in request.POST:
            # Handle delete logic
            user = request.user
            user.delete()

            reg = RegisterStudent.objects.filter(username=user)
            reg.delete()

            messages.success(request, 'Account deleted successfully.')
            
            return redirect('/')  
            print("delete")
        
        

    return render(request, 'settings\\settings.html')