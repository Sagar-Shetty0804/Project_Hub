"""Mark calculations shared by views, exports and PDFs."""

from collections import defaultdict
from decimal import Decimal

from .models import Remark, Score


def round_table(rnd, projects):
    """Build per-project/per-student mark rows for a round.

    Returns a list of dicts: {project, remark, students: [{student, marks: {criterion_id: Decimal}, total, complete}]}
    """
    criteria = list(rnd.rubric.criteria.all())
    scores = defaultdict(dict)
    for s in Score.objects.filter(round=rnd, project__in=projects):
        scores[s.student_id][s.criterion_id] = s.marks
    remarks = {r.project_id: r for r in Remark.objects.filter(round=rnd, project__in=projects)}

    rows = []
    for project in projects:
        students = []
        for member in project.members:
            marks = scores.get(member.id, {})
            students.append({
                "student": member,
                "marks": marks,
                "cells": [marks.get(c.id) for c in criteria],
                "total": sum(marks.values(), Decimal(0)),
                "complete": len(marks) == len(criteria) and bool(criteria),
            })
        rows.append({"project": project, "remark": remarks.get(project.id), "students": students})
    return criteria, rows


def progress(rnd):
    """(students fully marked, total students) for a round."""
    projects = list(rnd.projects().prefetch_related("memberships__student"))
    _, rows = round_table(rnd, projects)
    students = [s for r in rows for s in r["students"]]
    return sum(s["complete"] for s in students), len(students)


def student_results(student):
    """Published marks for a student, one entry per round."""
    from .models import ReviewRound

    results = []
    rounds = ReviewRound.objects.filter(results_published=True, scores__student=student).distinct()
    for rnd in rounds.select_related("rubric"):
        criteria = list(rnd.rubric.criteria.all())
        marks = {s.criterion_id: s.marks for s in Score.objects.filter(round=rnd, student=student)}
        project = Score.objects.filter(round=rnd, student=student).select_related("project").first().project
        remark = Remark.objects.filter(round=rnd, project=project).first()
        total = sum(marks.values(), Decimal(0))
        out_of = sum((c.max_marks for c in criteria), Decimal(0))
        results.append({
            "round": rnd, "project": project, "remark": remark,
            "rows": [{"criterion": c, "marks": marks.get(c.id)} for c in criteria],
            "total": total, "out_of": out_of,
            "percent": round(float(total) * 100 / float(out_of)) if out_of else 0,
        })
    return results
