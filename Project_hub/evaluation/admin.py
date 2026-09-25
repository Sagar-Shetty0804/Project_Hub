from django.contrib import admin

from .models import Criterion, Remark, ReviewRound, Rubric, Score


class CriterionInline(admin.TabularInline):
    model = Criterion
    extra = 1


@admin.register(Rubric)
class RubricAdmin(admin.ModelAdmin):
    inlines = [CriterionInline]


@admin.register(ReviewRound)
class ReviewRoundAdmin(admin.ModelAdmin):
    list_display = ["name", "project_type", "semester", "batch_year", "state", "results_published"]


admin.site.register([Score, Remark])
