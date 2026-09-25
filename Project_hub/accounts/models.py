from django.contrib.auth.models import AbstractUser
from django.db import models

from core.constants import BRANCHES, DIVISIONS


class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = "student", "Student"
        GUIDE = "guide", "Guide"
        EVALUATOR = "evaluator", "Evaluator"
        ADMIN = "admin", "Admin"

    role = models.CharField(max_length=12, choices=Role.choices, default=Role.STUDENT)
    email = models.EmailField(unique=True)

    # Student details
    roll_no = models.CharField(max_length=20, blank=True)
    branch = models.CharField(max_length=10, choices=BRANCHES, blank=True)
    division = models.CharField(max_length=2, choices=DIVISIONS, blank=True)

    # Faculty details
    designation = models.CharField(max_length=60, blank=True, help_text="e.g. Assistant Professor")

    avatar = models.ImageField(upload_to="avatars/", blank=True)
    bio = models.CharField(max_length=240, blank=True)

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT

    @property
    def is_guide(self):
        return self.role == self.Role.GUIDE

    @property
    def is_evaluator(self):
        return self.role == self.Role.EVALUATOR

    @property
    def is_admin_role(self):
        return self.is_superuser or self.role == self.Role.ADMIN

    @property
    def is_faculty(self):
        return self.role in (self.Role.GUIDE, self.Role.EVALUATOR, self.Role.ADMIN) or self.is_superuser

    @property
    def display_name(self):
        return self.get_full_name() or self.username

    @property
    def initials(self):
        parts = self.display_name.split()
        return "".join(p[0] for p in parts[:2]).upper() or "?"

    @property
    def class_label(self):
        """e.g. COMPS · B · 41"""
        return " · ".join(x for x in [self.branch, self.division, self.roll_no] if x)

    def __str__(self):
        return self.display_name
