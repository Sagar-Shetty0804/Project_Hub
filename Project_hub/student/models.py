from django.db import models
from Login_page.models import RegisterStudent
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_delete
from django.core.validators import FileExtensionValidator
import os

class CodeFile(models.Model):
    group_code = models.ForeignKey(RegisterStudent, on_delete=models.CASCADE, related_name="code_files", null=False)
    file = models.FileField(upload_to="uploads/code/")
    content = models.TextField(blank=True, null=True)  # To store file content as text
    upload_date = models.DateTimeField(auto_now_add=True)
    

    def save(self, *args, **kwargs):
        if not self.pk:
            super().save(*args, **kwargs)  # Save the file first

    # Read the content after saving the file
            if self.file:
                with self.file.open('rb') as f:  # Open file in read-binary mode
                    file_data = f.read()
                    try:
                        self.content = file_data.decode('utf-8')  # Try decoding as UTF-8
                    except UnicodeDecodeError:
                        self.content = file_data.decode('latin-1') 
        else:
             super().save(*args, **kwargs)
    def delete(self, *args, **kwargs):
        # Delete the file from the filesystem
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.group_code.groupCode} - Code File"



class DatabaseFile(models.Model):
    group_code = models.ForeignKey(RegisterStudent, on_delete=models.CASCADE, related_name="database_files")
    file = models.FileField(upload_to="uploads/database/")
    content = models.TextField(blank=True, null=True)
    upload_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.group_code.groupCode} - Database File"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Save the file first

    def delete(self, *args, **kwargs):
        # Delete the file from the filesystem
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        super().delete(*args, **kwargs)


class DocumentFile(models.Model):
    group_code = models.ForeignKey(RegisterStudent, on_delete=models.CASCADE, related_name="document_files")
    file = models.FileField(upload_to="uploads/document/", validators=[
        FileExtensionValidator(allowed_extensions=['pdf', 'ppt', 'pptx'])
    ])
    upload_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.group_code.groupCode} - Document File"

    



class AdditionalFile(models.Model):
    group_code = models.ForeignKey(RegisterStudent, on_delete=models.CASCADE, related_name="additional_files")
    file = models.FileField(upload_to="uploads/additional/", validators=[
        FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'mp4', 'mov', 'avi'])
    ])
    upload_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.group_code.groupCode} - Additional File"


