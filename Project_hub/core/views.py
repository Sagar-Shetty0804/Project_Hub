from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.text import slugify

from accounts.models import User
from core.constants import BRANCHES, PROJECT_TYPES
from core.permissions import role_required
from evaluation import services as eval_services
from evaluation.models import ReviewRound
from mentoring.models import Milestone, ProgressLog
from mentoring.views import guide_summary
from projects.models import Like, Project, ProjectFile

from . import pdf


def landing(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")
    stats = {
        "projects": Project.objects.count(),
        "students": User.objects.filter(role=User.Role.STUDENT).count(),
        "files": ProjectFile.objects.filter(is_latest=True).count(),
    }
    showcase = (
        Project.objects.filter(is_published=True)
        .prefetch_related("media")
        .order_by("-is_featured", "-updated_at")[:3]
    )
    return render(request, "core/landing.html", {"stats": stats, "showcase": showcase})


@login_required
def dashboard(request):
    user = request.user
    if user.is_admin_role:
        return redirect("core:insights")
    if user.is_guide:
        return _guide_dashboard(request)
    if user.is_evaluator:
        return _evaluator_dashboard(request)
    return _student_dashboard(request)


def _student_dashboard(request):
    user = request.user
    projects = list(
        Project.objects.filter(memberships__student=user)
        .select_related("guide")
        .prefetch_related("memberships__student", "media")
        .order_by("-batch_year", "-semester")
    )
    for p in projects:
        ms = list(p.milestones.all())
        p.ms_done = sum(m.status == Milestone.Status.APPROVED for m in ms)
        p.ms_total = len(ms)
        p.next_ms = next((m for m in ms if m.status != Milestone.Status.APPROVED), None)
        p.file_count = p.files.filter(is_latest=True).count()
    trending = (
        Project.objects.filter(is_published=True)
        .exclude(memberships__student=user)
        .annotate(like_count=Count("likes"))
        .prefetch_related("media", "memberships__student")
        .order_by("-like_count", "-updated_at")[:3]
    )
    liked = set(Like.objects.filter(user=user).values_list("project_id", flat=True))
    return render(request, "core/dash_student.html", {
        "projects": projects,
        "trending": trending,
        "liked": liked,
        "results": eval_services.student_results(user)[:3],
        "activity": user.notifications.all()[:6],
    })


def _guide_dashboard(request):
    user = request.user
    projects = list(guide_summary(user))
    today = timezone.localdate()
    upcoming = (
        Milestone.objects.filter(project__guide=user, due_date__isnull=False)
        .exclude(status=Milestone.Status.APPROVED)
        .select_related("project").order_by("due_date")[:6]
    )
    to_review = Milestone.objects.filter(project__guide=user, status=Milestone.Status.SUBMITTED).select_related("project")
    rounds = ReviewRound.objects.filter(state=ReviewRound.State.OPEN)
    rounds = [r for r in rounds if r.projects().filter(guide=user).exists()]
    return render(request, "core/dash_guide.html", {
        "projects": projects, "upcoming": upcoming, "to_review": to_review, "rounds": rounds,
        "today": today, "unassigned": Project.objects.filter(guide__isnull=True).count(),
        "recent_logs": ProgressLog.objects.filter(project__guide=user).select_related("project", "author")[:5],
    })


def _evaluator_dashboard(request):
    rounds = list(ReviewRound.objects.filter(state=ReviewRound.State.OPEN).select_related("rubric"))
    for r in rounds:
        r.done, r.total = eval_services.progress(r)
        r.pct = round(r.done * 100 / r.total) if r.total else 0
    recent = Project.objects.prefetch_related("media", "memberships__student").order_by("-updated_at")[:6]
    return render(request, "core/dash_evaluator.html", {"rounds": rounds, "recent": recent})


@role_required()
def insights(request):
    projects = Project.objects.all()
    counts = {
        "students": User.objects.filter(role=User.Role.STUDENT).count(),
        "faculty": User.objects.filter(role__in=[User.Role.GUIDE, User.Role.EVALUATOR]).count(),
        "projects": projects.count(),
        "files": ProjectFile.objects.filter(is_latest=True).count(),
        "storage": ProjectFile.objects.aggregate(s=Sum("size"))["s"] or 0,
        "no_guide": projects.filter(guide__isnull=True).count(),
    }

    def bars(field, choices):
        raw = dict(projects.values_list(field).annotate(n=Count("id")))
        items = [{"key": k, "label": label, "n": raw.get(k, 0)} for k, label in choices]
        top = max([i["n"] for i in items] + [1])
        for i in items:
            i["pct"] = round(i["n"] * 100 / top)
        return items

    rounds = list(ReviewRound.objects.select_related("rubric")[:6])
    for r in rounds:
        r.done, r.total = eval_services.progress(r)
        r.pct = round(r.done * 100 / r.total) if r.total else 0

    ms = Milestone.objects.aggregate(
        total=Count("id"),
        approved=Count("id", filter=Q(status=Milestone.Status.APPROVED)),
        waiting=Count("id", filter=Q(status=Milestone.Status.SUBMITTED)),
        overdue=Count("id", filter=Q(due_date__lt=timezone.localdate()) & Q(status__in=[Milestone.Status.PENDING, Milestone.Status.CHANGES])),
    )
    return render(request, "core/insights.html", {
        "counts": counts,
        "by_branch": bars("branch", BRANCHES),
        "by_type": bars("project_type", PROJECT_TYPES),
        "by_status": bars("status", Project.Status.choices),
        "rounds": rounds,
        "ms": ms,
        "guides": User.objects.filter(role=User.Role.GUIDE).annotate(n=Count("guided_projects")).order_by("-n")[:8],
        "recent": projects.prefetch_related("memberships__student").order_by("-created_at")[:6],
    })


# ------------------------------------------------------------------ PDFs ----

def _pdf_response(data, filename):
    resp = HttpResponse(data, content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp


@login_required
def certificate(request, code, user_id):
    project = get_object_or_404(Project, code=code)
    student = get_object_or_404(User, pk=user_id)
    viewer = request.user
    if not project.is_member(student):
        raise PermissionDenied
    if not (viewer == student or viewer.is_admin_role or project.guide_id == viewer.id):
        raise PermissionDenied
    if project.status != Project.Status.COMPLETED:
        raise PermissionDenied("Certificates are available once the project is marked completed.")
    results = [r for r in eval_services.student_results(student) if r["project"].id == project.id]
    data = pdf.certificate(project, student, results)
    return _pdf_response(data, f"certificate-{slugify(student.display_name)}.pdf")


@login_required
def report(request, code):
    project = get_object_or_404(Project.objects.select_related("guide"), code=code)
    if not project.can_view_private(request.user):
        raise PermissionDenied
    results = {m.id: [r for r in eval_services.student_results(m) if r["project"].id == project.id] for m in project.members}
    data = pdf.project_report(project, list(project.milestones.all()), results)
    return _pdf_response(data, f"{project.code}-report.pdf")
