from django.contrib import admin

from .models import Milestone, ProgressLog


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ["title", "project", "due_date", "status"]
    list_filter = ["status"]


admin.site.register(ProgressLog)
