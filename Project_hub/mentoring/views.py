from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.constants import BRANCHES, PROJECT_TYPES
from core.permissions import role_required
from notifications.utils import notify
from projects.models import Project

from .models import Milestone, ProgressLog


def _is_project_guide(user, project):
    return user.is_admin_role or (project.guide_id is not None and project.guide_id == user.id)


@role_required("guide")
def find_groups(request):
    """Projects without a guide, which the guide can adopt."""
    qs = Project.objects.filter(guide__isnull=True).prefetch_related("memberships__student")
    ptype, branch = request.GET.get("type", ""), request.GET.get("branch", "")
    if ptype:
        qs = qs.filter(project_type=ptype)
    if branch:
        qs = qs.filter(branch=branch)
    return render(request, "mentoring/find_groups.html", {
        "projects": qs.order_by("code"), "types": PROJECT_TYPES, "branches": BRANCHES,
        "f": {"type": ptype, "branch": branch},
    })


@role_required("guide")
@require_POST
def adopt(request):
    codes = request.POST.getlist("codes")
    projects = list(Project.objects.filter(code__in=codes, guide__isnull=True))
    for p in projects:
        p.guide = request.user
        p.save(update_fields=["guide"])
        Milestone.create_defaults(p)
        notify(p.members, f"{request.user.display_name} is now guiding {p.title}",
               reverse("mentoring:workspace", args=[p.code]), actor=request.user, email=True)
    if projects:
        messages.success(request, f"You're now guiding {len(projects)} project{'s' if len(projects) != 1 else ''}.")
    return redirect("core:dashboard")


@role_required("guide")
@require_POST
def release(request, code):
    project = get_object_or_404(Project, code=code)
    if not _is_project_guide(request.user, project):
        raise PermissionDenied
    project.guide = None
    project.save(update_fields=["guide"])
    messages.info(request, f"You're no longer guiding {project.title}.")
    return redirect("core:dashboard")


@login_required
def workspace(request, code):
    project = get_object_or_404(Project.objects.select_related("guide"), code=code)
    user = request.user
    if not project.can_view_private(user):
        raise PermissionDenied
    is_guide = _is_project_guide(user, project)
    is_member = project.is_member(user)
    ws_url = reverse("mentoring:workspace", args=[project.code])

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "log" and (is_guide or is_member) and request.POST.get("summary", "").strip():
            ProgressLog.objects.create(
                project=project, author=user,
                meeting_date=request.POST.get("meeting_date") or timezone.localdate(),
                summary=request.POST["summary"].strip(), next_steps=request.POST.get("next_steps", "").strip(),
            )
            notify(project.members + [project.guide], f"New progress log on {project.title}",
                   ws_url + "#logs", actor=user)
            messages.success(request, "Log added.")

        elif action == "submit" and is_member:
            m = get_object_or_404(project.milestones, pk=request.POST.get("milestone"))
            m.status = Milestone.Status.SUBMITTED
            m.submission_note = request.POST.get("note", "").strip()
            m.submitted_at = timezone.now()
            m.save()
            notify([project.guide], f"{project.title} submitted “{m.title}” for review",
                   ws_url, actor=user, email=True)
            messages.success(request, f"“{m.title}” sent to your guide.")

        elif action == "review" and is_guide:
            m = get_object_or_404(project.milestones, pk=request.POST.get("milestone"))
            decision = request.POST.get("decision")
            if decision in (Milestone.Status.APPROVED, Milestone.Status.CHANGES):
                m.status = decision
                m.feedback = request.POST.get("feedback", "").strip()
                m.reviewed_at = timezone.now()
                m.save()
                word = "approved" if decision == Milestone.Status.APPROVED else "needs changes"
                notify(project.members, f"“{m.title}” {word}", ws_url, actor=user, email=True)
                messages.success(request, f"“{m.title}” marked as {m.get_status_display().lower()}.")

        elif action == "milestone_save" and is_guide:
            pk = request.POST.get("milestone")
            m = get_object_or_404(project.milestones, pk=pk) if pk else Milestone(project=project, order=project.milestones.count())
            m.title = request.POST.get("title", "").strip()[:80] or m.title or "Untitled milestone"
            m.description = request.POST.get("description", "").strip()[:240]
            due = request.POST.get("due_date")
            try:
                m.due_date = date.fromisoformat(due) if due else None
            except ValueError:
                m.due_date = None
            m.save()
            if not pk:
                notify(project.members, f"New milestone “{m.title}” on {project.title}", ws_url, actor=user)
            messages.success(request, "Milestone saved.")

        elif action == "milestone_delete" and is_guide:
            get_object_or_404(project.milestones, pk=request.POST.get("milestone")).delete()
            messages.info(request, "Milestone removed.")

        elif action == "status" and (is_guide or is_member):
            status = request.POST.get("status")
            if status in Project.Status.values:
                project.status = status
                project.save(update_fields=["status"])
                messages.success(request, f"Project marked as {project.get_status_display().lower()}.")

        return redirect(ws_url)

    milestones = list(project.milestones.all())
    done = sum(m.status == Milestone.Status.APPROVED for m in milestones)
    return render(request, "mentoring/workspace.html", {
        "project": project,
        "milestones": milestones,
        "logs": project.logs.select_related("author"),
        "is_guide": is_guide,
        "is_member": is_member,
        "progress": round(done * 100 / len(milestones)) if milestones else 0,
        "done": done,
        "today": timezone.localdate(),
        "statuses": Project.Status.choices,
    })


def guide_summary(user):
    """Projects a guide mentors, with counts used on the dashboard."""
    return (
        Project.objects.filter(guide=user)
        .prefetch_related("memberships__student")
        .annotate(
            pending_reviews=Count("milestones", filter=Q(milestones__status=Milestone.Status.SUBMITTED), distinct=True),
            approved=Count("milestones", filter=Q(milestones__status=Milestone.Status.APPROVED), distinct=True),
            total_milestones=Count("milestones", distinct=True),
        )
        .order_by("-pending_reviews", "code")
    )
