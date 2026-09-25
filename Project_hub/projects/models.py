import hashlib
import posixpath
import secrets

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property

from core.constants import BRANCHES, PROJECT_TYPES, SEMESTERS

# Vault files live outside MEDIA_ROOT so they can never be fetched by URL;
# they are only served through a permission-checked view.
private_storage = FileSystemStorage(location=settings.BASE_DIR / "private_media")

IMAGE_EXTS = ["jpg", "jpeg", "png", "gif", "webp", "jfif"]
VIDEO_EXTS = ["mp4", "webm", "mov"]

# extension -> highlight.js language name
LANGUAGES = {
    "py": "python", "js": "javascript", "jsx": "javascript", "ts": "typescript", "tsx": "typescript",
    "html": "xml", "htm": "xml", "xml": "xml", "css": "css", "scss": "scss", "json": "json",
    "java": "java", "c": "c", "h": "c", "cpp": "cpp", "hpp": "cpp", "cs": "csharp", "go": "go",
    "rs": "rust", "php": "php", "rb": "ruby", "kt": "kotlin", "swift": "swift", "dart": "dart",
    "sql": "sql", "sh": "bash", "bat": "dos", "ps1": "powershell", "md": "markdown", "yml": "yaml",
    "yaml": "yaml", "ipynb": "json", "txt": "plaintext", "csv": "plaintext", "r": "r", "m": "matlab",
}


def generate_invite_code():
    return secrets.token_hex(3).upper()  # e.g. 4F9A1C


class Project(models.Model):
    class Status(models.TextChoices):
        PLANNING = "planning", "Planning"
        BUILDING = "building", "In progress"
        COMPLETED = "completed", "Completed"

    code = models.CharField(max_length=30, unique=True, editable=False)
    invite_code = models.CharField(max_length=6, unique=True, default=generate_invite_code)

    title = models.CharField(max_length=120)
    tagline = models.CharField(max_length=160, blank=True, help_text="One sentence that sells the project.")
    abstract = models.TextField(blank=True)
    tech_stack = models.CharField(max_length=200, blank=True, help_text="Comma separated, e.g. Django, React, SQLite")
    demo_url = models.URLField(blank=True, help_text="Optional live demo or video link")
    cover = models.ImageField(upload_to="covers/", blank=True)

    project_type = models.CharField(max_length=2, choices=PROJECT_TYPES)
    semester = models.PositiveSmallIntegerField(choices=SEMESTERS)
    batch_year = models.PositiveSmallIntegerField(help_text="Academic year the project runs in, e.g. 2025")
    branch = models.CharField(max_length=10, choices=BRANCHES)
    group_number = models.PositiveSmallIntegerField(editable=False)

    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PLANNING)
    guide = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="guided_projects", limit_choices_to={"role": "guide"},
    )
    is_published = models.BooleanField(default=True, help_text="Show the showcase page on Explore")
    is_featured = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def save(self, *args, **kwargs):
        if not self.code:
            siblings = Project.objects.filter(
                project_type=self.project_type, semester=self.semester,
                batch_year=self.batch_year, branch=self.branch,
            )
            self.group_number = (siblings.aggregate(m=models.Max("group_number"))["m"] or 0) + 1
            self.code = (
                f"{self.project_type}{self.semester}-{self.batch_year % 100:02d}-"
                f"{self.branch}-{self.group_number:02d}"
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.code})"

    def get_absolute_url(self):
        return reverse("projects:detail", args=[self.code])

    # ---- display helpers ----
    @property
    def tags(self):
        return [t.strip() for t in self.tech_stack.split(",") if t.strip()]

    @property
    def tone(self):
        """Stable 0-5 index used to pick a cover pattern colour."""
        return int(hashlib.md5(self.code.encode()).hexdigest(), 16) % 6

    @property
    def period_label(self):
        return f"{self.get_project_type_display()} · Sem {self.semester} · {self.batch_year}"

    @cached_property
    def members(self):
        return [m.student for m in self.memberships.select_related("student").order_by("-is_lead", "joined_at")]

    @cached_property
    def cover_image(self):
        """Uploaded cover, or the first gallery image."""
        if self.cover:
            return self.cover.url
        first = self.media.filter(kind=MediaItem.Kind.IMAGE).first()
        return first.file.url if first else None

    # ---- permissions ----
    def is_member(self, user):
        return user.is_authenticated and self.memberships.filter(student=user).exists()

    def is_lead(self, user):
        return user.is_authenticated and self.memberships.filter(student=user, is_lead=True).exists()

    def can_edit(self, user):
        return self.is_member(user) or (user.is_authenticated and user.is_admin_role)

    def can_view_private(self, user):
        """Code vault, comments, marks: team, their guide, evaluators and admins."""
        if not user.is_authenticated:
            return False
        return (
            self.is_member(user)
            or user.is_admin_role
            or user.is_evaluator
            or (self.guide_id is not None and self.guide_id == user.id)
        )


class Membership(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="memberships")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships")
    is_lead = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("project", "student")]

    def __str__(self):
        return f"{self.student} in {self.project.code}"


def vault_upload_to(instance, filename):
    return f"vault/{instance.project.code}/v{instance.version}/{instance.path}"


class ProjectFile(models.Model):
    """One version of one file in a project's private code vault."""

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="files")
    path = models.CharField(max_length=255, help_text="Path inside the project, e.g. src/app.py")
    file = models.FileField(upload_to=vault_upload_to, storage=private_storage, max_length=400)
    content = models.TextField(null=True, blank=True, help_text="Decoded text for text files")
    size = models.PositiveIntegerField(default=0)
    sha256 = models.CharField(max_length=64, db_index=True, blank=True)
    version = models.PositiveIntegerField(default=1)
    is_latest = models.BooleanField(default=True, db_index=True)
    note = models.CharField(max_length=160, blank=True, help_text="What changed in this version")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["path", "-version"]
        indexes = [models.Index(fields=["project", "path"])]

    def __str__(self):
        return f"{self.project.code}:{self.path} v{self.version}"

    @property
    def name(self):
        return posixpath.basename(self.path)

    @property
    def extension(self):
        return self.name.rsplit(".", 1)[-1].lower() if "." in self.name else ""

    @property
    def language(self):
        return LANGUAGES.get(self.extension, "plaintext")

    @property
    def is_text(self):
        return self.content is not None

    @property
    def is_image(self):
        return self.extension in IMAGE_EXTS + ["svg"]

    @property
    def is_pdf(self):
        return self.extension == "pdf"

    @property
    def line_count(self):
        return self.content.count("\n") + 1 if self.content else 0

    def history(self):
        return ProjectFile.objects.filter(project=self.project, path=self.path).order_by("-version")

    @staticmethod
    def hash_bytes(data):
        return hashlib.sha256(data).hexdigest()


class FileComment(models.Model):
    file = models.ForeignKey(ProjectFile, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    line = models.PositiveIntegerField(null=True, blank=True)
    body = models.TextField()
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class MediaItem(models.Model):
    """Photos and videos shown on the public showcase page."""

    class Kind(models.TextChoices):
        IMAGE = "image", "Image"
        VIDEO = "video", "Video"

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="media")
    kind = models.CharField(max_length=5, choices=Kind.choices)
    file = models.FileField(
        upload_to="showcase/",
        validators=[FileExtensionValidator(IMAGE_EXTS + VIDEO_EXTS)],
    )
    caption = models.CharField(max_length=140, blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "created_at"]


class Link(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="links")
    title = models.CharField(max_length=80)
    url = models.URLField()
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class Like(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("project", "user")]


class Bookmark(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="bookmarks")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookmarks")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("project", "user")]
        ordering = ["-created_at"]
