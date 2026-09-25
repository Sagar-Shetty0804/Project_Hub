from django import forms
from django.utils import timezone

from .models import ReviewRound, Rubric


class RubricForm(forms.ModelForm):
    class Meta:
        model = Rubric
        fields = ["name", "description"]


class ReviewRoundForm(forms.ModelForm):
    class Meta:
        model = ReviewRound
        fields = ["name", "rubric", "project_type", "semester", "batch_year", "branch", "review_date"]
        widgets = {"review_date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["batch_year"].initial = timezone.localdate().year
        self.fields["rubric"].queryset = Rubric.objects.order_by("name")
