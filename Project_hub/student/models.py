from django.db import models
from Login_page.models import RegisterStudent

class CodeFile(models.Model):
    group_code = models.ForeignKey(RegisterStudent, on_delete=models.CASCADE, related_name="code_files", null=False)
    file = models.FileField(upload_to="uploads/code/")
    content = models.TextField(blank=True, null=True)  # To store file content as text
    upload_date = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.group_code.groupCode} - Code File"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Save the file first

    # Read the content after saving the file
        if self.file:
        # Open the file in binary mode and decode it if needed
            with self.file.open('rb') as f:  # Open file in read-binary mode
                file_data = f.read()
                try:
                    self.content = file_data.decode('utf-8')  # Try decoding as UTF-8
                except UnicodeDecodeError:
                    self.content = file_data.decode('latin-1')  # Fallback to Latin-1 if UTF-8 fails

        super().save(*args, **kwargs)  # Save the updated content



class DatabaseFile(models.Model):
    group_code = models.ForeignKey(RegisterStudent, on_delete=models.CASCADE, related_name="database_files")
    file = models.FileField(upload_to="uploads/database/")
    content = models.TextField(blank=True, null=True)
    upload_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.group_code.groupCode} - Database File"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Save the file first

        # Read the content after saving the file
        if self.file:
            with self.file.open('r', encoding='utf-8') as f:
                self.content = f.read()

        super().save(*args, **kwargs)


class DocumentFile(models.Model):
    group_code = models.ForeignKey(RegisterStudent, on_delete=models.CASCADE, related_name="document_files")
    file = models.FileField(upload_to="uploads/document/")
    content = models.TextField(blank=True, null=True)
    upload_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.group_code.groupCode} - Document File"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.file:
            with self.file.open('r', encoding='utf-8') as f:
                self.content = f.read()

        super().save(*args, **kwargs)


class AdditionalFile(models.Model):
    group_code = models.ForeignKey(RegisterStudent, on_delete=models.CASCADE, related_name="additional_files")
    file = models.FileField(upload_to="uploads/additional/")
    content = models.TextField(blank=True, null=True)
    upload_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.group_code.groupCode} - Additional File"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.file:
            with self.file.open('r', encoding='utf-8') as f:
                self.content = f.read()

        super().save(*args, **kwargs)

