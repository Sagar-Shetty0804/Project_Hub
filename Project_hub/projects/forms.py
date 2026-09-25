from django import forms
from django.utils import timezone

from .models import Link, Project


class ProjectCreateForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["title", "tagline", "project_type", "semester", "batch_year", "branch", "tech_stack", "abstract"]
        widgets = {"abstract": forms.Textarea(attrs={"rows": 5})}

    def __init__(self, *args, student=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.student = student
        self.fields["batch_year"].initial = timezone.localdate().year
        if student and student.branch:
            self.fields["branch"].initial = student.branch

    def clean(self):
        data = super().clean()
        if self.student and all(k in data for k in ("project_type", "semester", "batch_year")):
            clash = Project.objects.filter(
                memberships__student=self.student,
                project_type=data["project_type"], semester=data["semester"], batch_year=data["batch_year"],
            )
            if clash.exists():
                raise forms.ValidationError(
                    f"You're already in a project for this semester: {clash.first().title}."
                )
        return data


class ProjectEditForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["title", "tagline", "abstract", "tech_stack", "demo_url", "cover", "status", "is_published"]
        widgets = {"abstract": forms.Textarea(attrs={"rows": 7})}
        labels = {"is_published": "Show this project on Explore"}


class JoinProjectForm(forms.Form):
    invite_code = forms.CharField(
        max_length=6, min_length=6,
        widget=forms.TextInput(attrs={"placeholder": "e.g. 4F9A1C", "autocomplete": "off", "class": "code-input"}),
    )

    def clean_invite_code(self):
        return self.cleaned_data["invite_code"].strip().upper()


class LinkForm(forms.ModelForm):
    class Meta:
        model = Link
        fields = ["title", "url"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "e.g. Research paper"}),
            "url": forms.URLInput(attrs={"placeholder": "https://"}),
        }
