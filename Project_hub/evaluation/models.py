from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from core.constants import BRANCHES, PROJECT_TYPES, SEMESTERS
from projects.models import Project


class Rubric(models.Model):
    name = models.CharField(max_length=80)
    description = models.CharField(max_length=240, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @property
    def total_marks(self):
        return sum((c.max_marks for c in self.criteria.all()), Decimal(0))


class Criterion(models.Model):
    rubric = models.ForeignKey(Rubric, on_delete=models.CASCADE, related_name="criteria")
    name = models.CharField(max_length=60)
    description = models.CharField(max_length=200, blank=True)
    max_marks = models.DecimalField(max_digits=5, decimal_places=1, validators=[MinValueValidator(Decimal("0.5"))])
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.name} (/{self.max_marks})"


class ReviewRound(models.Model):
    """One evaluation event, e.g. "Mid-sem review" for all final-year major projects."""

    class State(models.TextChoices):
        OPEN = "open", "Open for marking"
        LOCKED = "locked", "Locked"

    name = models.CharField(max_length=80)
    rubric = models.ForeignKey(Rubric, on_delete=models.PROTECT, related_name="rounds")
    project_type = models.CharField(max_length=2, choices=PROJECT_TYPES)
    semester = models.PositiveSmallIntegerField(choices=SEMESTERS)
    batch_year = models.PositiveSmallIntegerField()
    branch = models.CharField(max_length=10, choices=BRANCHES, blank=True, help_text="Leave blank for all branches")
    review_date = models.DateField(null=True, blank=True)

    state = models.CharField(max_length=8, choices=State.choices, default=State.OPEN)
    results_published = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    @property
    def is_open(self):
        return self.state == self.State.OPEN

    def projects(self):
        qs = Project.objects.filter(
            project_type=self.project_type, semester=self.semester, batch_year=self.batch_year
        )
        if self.branch:
            qs = qs.filter(branch=self.branch)
        return qs

    def scope_label(self):
        parts = [self.get_project_type_display(), f"Sem {self.semester}", str(self.batch_year)]
        if self.branch:
            parts.append(self.branch)
        return " · ".join(parts)

    def can_mark(self, user, project):
        if not self.is_open or not user.is_authenticated:
            return False
        return user.is_admin_role or user.is_evaluator or (user.is_guide and project.guide_id == user.id)


class Score(models.Model):
    round = models.ForeignKey(ReviewRound, on_delete=models.CASCADE, related_name="scores")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="scores")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="scores")
    criterion = models.ForeignKey(Criterion, on_delete=models.CASCADE)
    marks = models.DecimalField(max_digits=5, decimal_places=1)
    marked_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("round", "student", "criterion")]


class Remark(models.Model):
    round = models.ForeignKey(ReviewRound, on_delete=models.CASCADE, related_name="remarks")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="remarks")
    text = models.TextField(blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("round", "project")]
