from django.shortcuts import render,redirect
from Login_page.models import RegisterStudent
from django.contrib import messages
from django.contrib.auth.models import User,Group
from django.contrib.auth import authenticate,login,logout
from services import authenticate_google_sheets

import os
from google.oauth2 import service_account
from googleapiclient.discovery import build


# Create your views here.

creds = service_account.Credentials.from_service_account_file(
        'project-hub-440106-e8621f99a378.json',
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )

service = build('sheets', 'v4', credentials=creds)

def addStudentData(data_dict):
    if data_dict is not None:
        spreadsheet_id = '1YnqOlaZKP39wvaWfyawIa1ips3y2aDUQrZhXNgP64g4'
        sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheets = sheet_metadata.get('sheets', '')

        # Determine sheet name based on projYear
        projeYear = data_dict['projYear']
        if projeYear in ['MI1', 'MI2']:
            sheet_name = 'mini project'
        elif projeYear in ['MN1', 'MN2']:
            sheet_name = 'minor project'
        elif projeYear in ['MA1', 'MA2']:
            sheet_name = 'major project'

        # Retrieve sheet ID for the identified sheet name
        sheet_id = None
        for sheet in sheets:
            if sheet.get("properties", {}).get("title") == sheet_name:
                sheet_id = sheet.get("properties", {}).get("sheetId")
                break

        if sheet_id is None:
            print("Sheet not found")
            return

        # Retrieve values from the sheet to find the row with the matching group code
        range_name = f"{sheet_name}!A2:C"  # Define range covering columns A to C
        result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
        values = result.get('values', [])

        # Find the row where the group code matches
        found = False
        start_row = None
        for i, row in enumerate(values, start=2):  # Start=2 to account for header row
            if row and row[0] == data_dict['groupCode']:
                start_row = i
                found = True
                break

        if not found:
            print(f"Group code '{data_dict['groupCode']}' not found in the sheet.")
            return

        # Find the first empty cell in column C for the matched group code row
        current_row = start_row
        while True:
            cell_range = f"{sheet_name}!C{current_row}"
            cell_value = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=cell_range).execute()
            if 'values' not in cell_value:
                # Empty cell found, add the new member here
                new_member_name = data_dict['name']
                update_body = {
                    "values": [[new_member_name]]  # Ensure it's a list of lists
                }
                service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=cell_range,
                    valueInputOption="RAW",
                    body=update_body
                ).execute()
                
                print(f"Added member '{new_member_name}' to group '{data_dict['groupCode']}' in row {current_row}.")
                break
            
            current_row += 1  # Move to the next row in column C if the cell is not empty




def mergecell(data_dict):

    if data_dict is not None:
        spreadsheet_id = '1YnqOlaZKP39wvaWfyawIa1ips3y2aDUQrZhXNgP64g4'
        sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheets = sheet_metadata.get('sheets', '')
        projeYear = data_dict['projYear']

        # Determine sheet name based on projYear
        if projeYear in ['MI1', 'MI2']:
            sheet_name = 'mini project'
        elif projeYear in ['MN1', 'MN2']:
            sheet_name = 'minor project'
        elif projeYear in ['MA1', 'MA2']:
            sheet_name = 'major project'

        # Retrieve the correct sheet ID
        sheet_id = None
        for sheet in sheets:
            if sheet.get("properties", {}).get("title") == sheet_name:
                sheet_id = sheet.get("properties", {}).get("sheetId")
                break

        if sheet_id is None:
            print("Sheet not found")
            return

        sheet = service.spreadsheets()

        # Starting row and end row for merging cells in sets of 4 rows
        start_row = 2
        end_row = start_row + 3

        # Finding the next set of 4 empty cells
        while True:
            range_name = f"{sheet_name}!A{start_row}:D{end_row}"
            result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
            values = result.get('values', [])

            if not values:  # If cells are empty, break the loop to merge them
                break

            # Move to the next set of 4 cells
            start_row += 4
            end_row = start_row + 3

        # Merge and populate columns A, B, and C with data for groupCode, projectName, and name
        for col, key in zip([0, 1, 2], ['groupCode', 'projectName', 'name']):
            # Define the merge request
            if col != 2:
                merge_request = {
                    "requests": [
                        {
                            "mergeCells": {
                                "range": {
                                    "sheetId": sheet_id,
                                    "startRowIndex": start_row - 1,
                                    "endRowIndex": end_row,
                                    "startColumnIndex": col,
                                    "endColumnIndex": col + 1,
                                },
                                "mergeType": "MERGE_ALL"
                            }
                        }
                    ]
                }
                sheet.batchUpdate(spreadsheetId=spreadsheet_id, body=merge_request).execute()

            # Add data to the merged cell
            data = [
                {
                    'range': f"{sheet_name}!{chr(65 + col)}{start_row}",
                    'values': [[data_dict[key]]]
                }
            ]
            body = {
                'valueInputOption': "RAW",
                'data': data
            }
            sheet.values().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()



def addProjectName(request):
    
    
    if  request.method == 'GET':
        projName = request.GET.get('projectName')
        request.method = 'COMPLETED'  
        if projName != None:      
            register = RegisterStudent.objects.filter(groupCode = groupCode)[0]
            
            data_dict = {'projectName':projName,
                        'groupCode':groupCode,
                        'projYear':register.projYear,
                        'name':register.name}

            register.projectName = projName
            register.save()
            mergecell(data_dict)
            messages.success(request,"Registration Successful")
            
            
            
            
        
        
    return render(request,'addProjectName.html')

def studentLogin(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        if User.objects.filter(username = username,groups__name = 'Student'):
            print("entered")
            user = authenticate(username = username,password = password)
            if user is not None:
                login(request,user)
                #guide page
                return redirect('/studentPage/')
            else:
                messages.warning(request, "incorrect password")
                print("fail")
        else:
            messages.warning(request, "Username not present for Student")

    return render(request,'studentLogin.html')

def registerStudent(request):
    
    print(request.method)
    if request.method == "POST":
        name = request.POST.get('name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        email = str(email)
        password = request.POST.get('password')
        confirmPassword = request.POST.get('confirmPassword')
        projYear = request.POST.get('projYear')
        year = request.POST.get('year')
        year = int(year) % 2000
        branch = request.POST.get('branch')
        groupNumber = request.POST.get('groupNumber')

        global groupCode
        groupCode = projYear+'_'+str(year)+'_'+branch+'_'+groupNumber

        checkuser = RegisterStudent.objects.filter(username = username).count()
        checkuser2 = RegisterStudent.objects.filter(email = email).count()
        
        if checkuser == 0:
            if checkuser2 == 0:
            
                if len(password) < 8:
                    messages.warning(request, "Password should have more than 8 characters")
                elif ('@somaiya.edu' in email) == False:
                    messages.warning(request, "Email should have '@somaiya.edu'")

                elif password == confirmPassword :

                    register = RegisterStudent(name=name ,username=username ,email=email ,year = year,branch = branch,groupNumber = groupNumber,groupCode = groupCode,projYear = projYear)
                    register.save()

                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password
                    )
                    user.save()

                    group = Group.objects.get(name = 'Student')
                    user.groups.add(group)

                    projName = RegisterStudent.objects.filter(groupCode = groupCode).values_list()
                    
                    projectName = projName[0][7]
                    if(projectName == 'blank'):
                        
                        return redirect('/addProjectName/')
                    else:
                        projN = RegisterStudent.objects.filter(groupCode = groupCode)[0]
                        temp = projN.projectName
                        register = RegisterStudent.objects.filter(username = username)[0]
                        register.projectName = temp
                        register.save()

                        data_dict = {'projectName':temp,
                                     'name':name,
                                     'groupCode':groupCode,
                                     'projYear':projYear,
                                    }
                        addStudentData(data_dict)

                    messages.success(request, "Registration succesfull")
                else:
                    messages.warning(request, "Password does not match")
            else:
                messages.warning(request, "Email already taken")
        else:
            messages.warning(request, "Username already taken")
    return render(request,'registerStudent.html')

def guideLogin(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        if User.objects.filter(username = username,groups__name = 'Guide'):
            print("entered")
            user = authenticate(username = username,password = password)
            if user is not None:
                login(request,user)
                #guide page
                return redirect('/guide/')
            else:
                messages.warning(request, "incorrect password")
                print("fail")
        else:
            messages.warning(request, "Username not present for guide")
            # if User.objects.filter(username = username,password = password).count() != 0:

            #     return render(request,'tp.html')
            # else:
            #     print("fail")

    #return render(request,'tp.html',{'users':user})
    return render(request,'guideLogin.html')


def evaluatorLogin(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        if User.objects.filter(username = username,groups__name = 'Evaluator'):
            print("entered")
            user = authenticate(username = username,password = password)
            if user is not None:
                login(request,user)
                #evaluator page
                return redirect('/evaluator/')
            else:
                messages.warning(request, "incorrect password")
                print("fail")
        else:
            messages.warning(request, "Username not present for evaluator")   
    return render(request,'evaluatorLogin.html')

