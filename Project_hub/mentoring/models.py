from django.conf import settings
from django.db import models
from django.utils import timezone

from projects.models import Project

DEFAULT_MILESTONES = [
    ("Synopsis", "Problem statement, objectives and proposed approach."),
    ("Design review", "Architecture, database design and UI wireframes."),
    ("Mid-term demo", "Working prototype of the core features."),
    ("Final submission", "Complete code, report and presentation."),
]


class Milestone(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Not submitted"
        SUBMITTED = "submitted", "Awaiting review"
        CHANGES = "changes", "Changes requested"
        APPROVED = "approved", "Approved"

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="milestones")
    title = models.CharField(max_length=80)
    description = models.CharField(max_length=240, blank=True)
    due_date = models.DateField(null=True, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    submission_note = models.TextField(blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["order", "due_date", "id"]

    def __str__(self):
        return f"{self.project.code}: {self.title}"

    @property
    def is_overdue(self):
        return (
            self.due_date is not None
            and self.status in (self.Status.PENDING, self.Status.CHANGES)
            and self.due_date < timezone.localdate()
        )

    @classmethod
    def create_defaults(cls, project):
        if not project.milestones.exists():
            cls.objects.bulk_create(
                [cls(project=project, title=t, description=d, order=i) for i, (t, d) in enumerate(DEFAULT_MILESTONES)]
            )


class ProgressLog(models.Model):
    """A meeting note / weekly log written by the guide or the team."""

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="logs")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    meeting_date = models.DateField(default=timezone.localdate)
    summary = models.TextField(help_text="What was discussed or done")
    next_steps = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-meeting_date", "-created_at"]
