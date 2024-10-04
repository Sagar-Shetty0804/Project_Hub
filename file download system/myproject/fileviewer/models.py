from django.db import models
from django.contrib.auth.models import User

class Folder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}/{self.name}"

class File(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name="files", null=True, blank=True)
    name = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}/{self.folder.name}/{self.name}" if self.folder else f"{self.user.username}/{self.name}"
