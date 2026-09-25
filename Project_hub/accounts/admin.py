from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class ProjectHubUserAdmin(UserAdmin):
    list_display = ["username", "email", "first_name", "last_name", "role", "branch"]
    list_filter = ["role", "branch", "is_staff"]
    fieldsets = UserAdmin.fieldsets + (
        ("ProjectHub", {"fields": ["role", "roll_no", "branch", "division", "designation", "avatar", "bio"]}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("ProjectHub", {"fields": ["email", "role", "first_name", "last_name"]}),
    )
