from django.shortcuts import render
from django.core.mail import send_mail
from django.conf import settings
from Login_page.models import RegisterStudent as reg
from django.contrib.auth.models import User
from guide.models import guide_groups,guideCommnets
from django.shortcuts import render,get_object_or_404,redirect
from Login_page.models import RegisterStudent
from student.models import CodeFile,DatabaseFile,AdditionalFile,DocumentFile
from django.shortcuts import redirect
from django.contrib import messages
from guide.models import guide_groups

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# Create your views here.
GOOGLE_SHEET_URL = 'https://docs.google.com/spreadsheets/d/1YnqOlaZKP39wvaWfyawIa1ips3y2aDUQrZhXNgP64g4/edit'
def table(request):
    return redirect(GOOGLE_SHEET_URL)
    return render(request,'table.html')
def start(request):

    return render(request,'guide.html')

def groups(request):
    currentUser = request.user

    data = guide_groups.objects.filter(guide_name = currentUser)
    data_dict = {'data':data}
    return render(request,'groups\\groups.html',data_dict)

def addGroup(request):
    currentUser = request.user
    
    
    data = reg.objects.values('groupCode','projectName').distinct()

    data_dict = {'data':data}

    if request.method == 'POST':
        
        groupCode = request.POST.getlist('code')
        
        
        for gc in groupCode:
            text = gc.split(',')
            print(text)
            
            register2 = guide_groups(groupCode = text[0],guide_name = currentUser,projectName = text[1])
            
            register2.save()

    return render(request,'addGroup\\addGroup.html',data_dict)

def studentView(request):
    data = request.GET['button_value']
    print(data)
    gc = RegisterStudent.objects.filter(groupCode = data).values_list("username")
    register_student = gc[0][0]
    code_files = CodeFile.objects.filter(group_code=register_student)
    database_files = DatabaseFile.objects.filter(group_code=register_student)
    document_files = DocumentFile.objects.filter(group_code=register_student)
    additional_files = AdditionalFile.objects.filter(group_code=register_student)

    print(code_files,database_files,document_files,additional_files)
    context = {
        'code_files': code_files,
        'database_files': database_files,
        'document_files': document_files,
        'additional_files': additional_files,
    }
    return render(request,'groups\\studentView.html',context)

def view_file_content_guide(request, file_type, file_id):
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
        comment = request.POST.get('comment')
        register_student = file_obj.group_code
        user_email = register_student.email
        register = guideCommnets(group_code = register_student.groupCode,comment = comment,file_type = file_type,guide_name = request.user,fileName = file_obj.file.name)
        register.save()
        subject = f"New Comment on Your {file_type.capitalize()} File"
        message = f"{request.user.username} commented on your {file_type} file: {file_obj.file.name}\n\nComment: {comment}"
        
        send_mail(
            subject,
            message,
            'projecthub338@gmail.com',  # From email (should be your EMAIL_HOST_USER)
            [register_student.email],  # Recipient's email address
            fail_silently=False,
        )

    
    return render(request, 'groups\\view_file_content_guide.html', {'file': file_obj, 'file_type': file_type})

def delete_selected_groups(request):
    if request.method == 'POST':
        selected_groups = request.POST.getlist('selected_groups')
        
        if selected_groups:
            guide_groups.objects.filter(groupCode__in=selected_groups).delete()
            messages.success(request, "Selected groups deleted successfully.")
        else:
            messages.warning(request, "No groups selected for deletion.")
        
    return redirect('guide:groups')