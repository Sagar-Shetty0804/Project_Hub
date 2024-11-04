from django import forms
from django.contrib import admin
from .models import CodeFile, DatabaseFile, DocumentFile, AdditionalFile, reference
from Login_page.models import RegisterStudent

class FileAdminForm(forms.ModelForm):
    content = forms.CharField(widget=forms.Textarea, required=False)  # To edit the file content

    class Meta:
        model = CodeFile
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(FileAdminForm, self).__init__(*args, **kwargs)
        self.fields['group_code'].queryset = RegisterStudent.objects.all()
        self.fields['group_code'].label_from_instance = lambda obj: obj.groupCode


class FileAdmin(admin.ModelAdmin):
    form = FileAdminForm
    list_filter = ('group_code__groupCode', 'upload_date')
    list_display = ('get_group_code', 'file', 'upload_date')

    def get_group_code(self, obj):
        return obj.group_code.groupCode

    get_group_code.short_description = 'Group Code'


# Register the models with the customized admin form
admin.site.register(CodeFile, FileAdmin)
admin.site.register(DatabaseFile, FileAdmin)
admin.site.register(DocumentFile, FileAdmin)
admin.site.register(AdditionalFile, FileAdmin)
admin.site.register(reference)