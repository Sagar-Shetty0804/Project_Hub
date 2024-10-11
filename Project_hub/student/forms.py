from django import forms
from .models import CodeFile, DatabaseFile, DocumentFile, AdditionalFile
from Login_page.models import RegisterStudent
class CodeFileUploadForm(forms.ModelForm):
    class Meta:
        model = CodeFile
        fields = ['file']

class DatabaseFileUploadForm(forms.ModelForm):
    class Meta:
        model = DatabaseFile
        fields = [ 'file']

class DocumentFileUploadForm(forms.ModelForm):
    class Meta:
        model = DocumentFile
        fields = [ 'file']

class AdditionalFileUploadForm(forms.ModelForm):
    class Meta:
        model = AdditionalFile
        fields = [ 'file']




