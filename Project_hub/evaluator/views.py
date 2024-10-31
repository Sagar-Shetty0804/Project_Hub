from django.shortcuts import render,get_object_or_404,redirect
from Login_page.models import RegisterStudent
from student.models import CodeFile,DatabaseFile,AdditionalFile,DocumentFile

# Create your views here.
GOOGLE_SHEET_URL = 'https://docs.google.com/spreadsheets/d/1YnqOlaZKP39wvaWfyawIa1ips3y2aDUQrZhXNgP64g4/edit'

def table(request):
    return redirect(GOOGLE_SHEET_URL)
    return render(request,'table.html')
def studentGroups(request):
    data = RegisterStudent.objects.all().values('groupCode','projectName').distinct()
    if request.method == "POST":
        sem = request.POST.get('sem')
        branch = request.POST.get('branch')
        # print(sem,branch)

        if sem != None and branch != None:
            data = RegisterStudent.objects.filter(projYear = sem,branch = branch).values('groupCode','projectName').distinct()
            # print(1)
            # print(data)
        elif sem != None:
            data = RegisterStudent.objects.filter(projYear = sem).values('groupCode','projectName').distinct()
            # print(2)
            # print(data)
        elif branch != None:
            data = RegisterStudent.objects.filter(branch = branch).values('groupCode','projectName').distinct()
            # print(3)
            # print(data)
    data_dict = {'data':data}
    # print(data_dict)
    return render(request,'studentGroup.html',data_dict)

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
    return render(request,'studentView.html',context)

def view_file_content_eval(request, file_type, file_id):
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
    
    if request.method == 'GET':
        logBookMarks = request.GET.get('logBookMarks')
        projectReport = request.GET.get('projectReport')
        studentEffort = request.GET.get('studentEffort')
        if logBookMarks != None and projectReport != None and studentEffort != None:
            print(logBookMarks,projectReport,studentEffort)
    return render(request, 'evalFileView.html', {'file': file_obj, 'file_type': file_type})
