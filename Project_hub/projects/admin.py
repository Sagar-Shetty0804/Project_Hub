from django.contrib import admin

from .models import Bookmark, FileComment, Like, Link, MediaItem, Membership, Project, ProjectFile


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["code", "title", "guide", "status", "is_published", "is_featured"]
    list_filter = ["project_type", "branch", "batch_year", "status", "is_featured"]
    search_fields = ["code", "title", "tech_stack"]
    inlines = [MembershipInline]


@admin.register(ProjectFile)
class ProjectFileAdmin(admin.ModelAdmin):
    list_display = ["path", "project", "version", "is_latest", "size", "uploaded_at"]
    list_filter = ["is_latest"]
    search_fields = ["path", "project__code"]


admin.site.register([MediaItem, Link, Like, Bookmark, FileComment])
