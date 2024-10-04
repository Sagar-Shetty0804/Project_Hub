from django import forms
from .models import File, Folder

class FolderForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = ['name']

class FileUploadForm(forms.ModelForm):
    folder = forms.ModelChoiceField(
        queryset=Folder.objects.none(), required=False, label="Select Folder"
    )

    class Meta:
        model = File
        fields = ['name', 'content', 'folder']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(FileUploadForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['folder'].queryset = Folder.objects.filter(user=user)
class FileEditForm(forms.ModelForm):
    class Meta:
        model = File
        fields = ['name', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 20, 'cols': 100}),
        }