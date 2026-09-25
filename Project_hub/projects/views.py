import difflib
import mimetypes

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_POST

from core.constants import BRANCHES, PROJECT_TYPES
from core.permissions import role_required
from notifications.utils import notify

from . import vault
from .forms import JoinProjectForm, LinkForm, ProjectCreateForm, ProjectEditForm
from .models import (
    IMAGE_EXTS,
    VIDEO_EXTS,
    Bookmark,
    FileComment,
    Like,
    Link,
    MediaItem,
    Membership,
    Project,
    ProjectFile,
    generate_invite_code,
)


def _project_for(request, code, need="view"):
    """Fetch a project and enforce access. need: view | private | edit | lead."""
    project = get_object_or_404(Project.objects.select_related("guide"), code=code)
    user = request.user
    allowed = {
        "view": project.is_published or project.can_view_private(user),
        "private": project.can_view_private(user),
        "edit": project.can_edit(user),
        "lead": project.is_lead(user) or user.is_admin_role,
    }[need]
    if not allowed:
        raise PermissionDenied
    return project


def _is_ajax(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


# ---------------------------------------------------------------- explore ----

@login_required
def explore(request):
    qs = (
        Project.objects.filter(is_published=True)
        .select_related("guide")
        .prefetch_related("memberships__student", "media")
        .annotate(like_count=Count("likes", distinct=True))
    )
    q = request.GET.get("q", "").strip()
    ptype = request.GET.get("type", "")
    branch = request.GET.get("branch", "")
    year = request.GET.get("year", "")
    tag = request.GET.get("tag", "").strip()
    sort = request.GET.get("sort", "recent")

    if q:
        qs = qs.filter(
            Q(title__icontains=q) | Q(tagline__icontains=q) | Q(abstract__icontains=q)
            | Q(tech_stack__icontains=q) | Q(code__icontains=q)
            | Q(memberships__student__first_name__icontains=q)
        ).distinct()
    if ptype:
        qs = qs.filter(project_type=ptype)
    if branch:
        qs = qs.filter(branch=branch)
    if year.isdigit():
        qs = qs.filter(batch_year=int(year))
    if tag:
        qs = qs.filter(tech_stack__icontains=tag)

    qs = {
        "popular": qs.order_by("-like_count", "-updated_at"),
        "title": qs.order_by("title"),
    }.get(sort, qs.order_by("-is_featured", "-created_at"))

    page = Paginator(qs, 12).get_page(request.GET.get("page"))
    liked = set(Like.objects.filter(user=request.user).values_list("project_id", flat=True))
    featured = (
        Project.objects.filter(is_published=True, is_featured=True).prefetch_related("media")[:3]
        if not any([q, ptype, branch, year, tag]) and page.number == 1 else []
    )
    years = Project.objects.order_by("-batch_year").values_list("batch_year", flat=True).distinct()

    # Popular tags for quick filters
    tag_counts = {}
    for stack in Project.objects.filter(is_published=True).values_list("tech_stack", flat=True):
        for t in {x.strip() for x in stack.split(",") if x.strip()}:
            tag_counts[t] = tag_counts.get(t, 0) + 1
    top_tags = sorted(tag_counts, key=lambda t: (-tag_counts[t], t.lower()))[:10]

    params = request.GET.copy()
    params.pop("page", None)
    return render(request, "projects/explore.html", {
        "page": page, "featured": featured, "liked": liked,
        "types": PROJECT_TYPES, "branches": BRANCHES, "years": years, "top_tags": top_tags,
        "f": {"q": q, "type": ptype, "branch": branch, "year": year, "tag": tag, "sort": sort},
        "querystring": params.urlencode(),
    })


@login_required
def bookmarks(request):
    saved = (
        Project.objects.filter(bookmarks__user=request.user)
        .prefetch_related("memberships__student", "media")
        .annotate(like_count=Count("likes", distinct=True))
        .order_by("-bookmarks__created_at")
    )
    liked = set(Like.objects.filter(user=request.user).values_list("project_id", flat=True))
    return render(request, "projects/bookmarks.html", {"projects": saved, "liked": liked})


# ------------------------------------------------------- create / join -------

@role_required("student")
def create(request):
    form = ProjectCreateForm(request.POST or None, student=request.user)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            project = form.save()
            Membership.objects.create(project=project, student=request.user, is_lead=True)
        messages.success(request, f"Project created. Share invite code {project.invite_code} with your teammates.")
        return redirect("projects:team", code=project.code)
    return render(request, "projects/create.html", {"form": form})


@role_required("student")
def join(request):
    form = JoinProjectForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        project = Project.objects.filter(invite_code=form.cleaned_data["invite_code"]).first()
        if project is None:
            form.add_error("invite_code", "No project uses that invite code. Check it with your team lead.")
        elif project.is_member(request.user):
            return redirect(project)
        elif project.memberships.count() >= settings.MAX_TEAM_SIZE:
            form.add_error("invite_code", f"That team already has {settings.MAX_TEAM_SIZE} members.")
        elif Project.objects.filter(
            memberships__student=request.user, project_type=project.project_type,
            semester=project.semester, batch_year=project.batch_year,
        ).exists():
            form.add_error("invite_code", "You're already in another project for that semester.")
        else:
            Membership.objects.create(project=project, student=request.user)
            notify(project.members + [project.guide], f"{request.user.display_name} joined {project.title}",
                   project.get_absolute_url(), actor=request.user)
            messages.success(request, f"You joined {project.title}.")
            return redirect(project)
    return render(request, "projects/join.html", {"form": form})


# ------------------------------------------------------------- showcase ------

@login_required
def detail(request, code):
    project = _project_for(request, code, "view")
    user = request.user
    images = [m for m in project.media.all() if m.kind == MediaItem.Kind.IMAGE]
    videos = [m for m in project.media.all() if m.kind == MediaItem.Kind.VIDEO]
    ctx = {
        "project": project,
        "images": images,
        "videos": videos,
        "links": project.links.all(),
        "like_count": project.likes.count(),
        "liked": project.likes.filter(user=user).exists(),
        "bookmarked": project.bookmarks.filter(user=user).exists(),
        "can_edit": project.can_edit(user),
        "can_private": project.can_view_private(user),
        "link_form": LinkForm(),
    }
    if ctx["can_private"]:
        ctx["file_count"] = project.files.filter(is_latest=True).count()
        ctx["milestones"] = project.milestones.all()
    return render(request, "projects/detail.html", ctx)


@login_required
def edit(request, code):
    project = _project_for(request, code, "edit")
    form = ProjectEditForm(request.POST or None, request.FILES or None, instance=project)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Project details saved.")
        return redirect(project)
    return render(request, "projects/edit.html", {"project": project, "form": form})


@login_required
def team(request, code):
    project = _project_for(request, code, "private")
    is_lead = project.is_lead(request.user) or request.user.is_admin_role

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "regenerate" and is_lead:
            project.invite_code = generate_invite_code()
            project.save(update_fields=["invite_code"])
            messages.success(request, "New invite code generated. The old one no longer works.")
        elif action == "remove" and is_lead:
            m = get_object_or_404(project.memberships, pk=request.POST.get("membership"))
            if m.is_lead:
                messages.error(request, "Transfer the lead role before removing the lead.")
            else:
                notify([m.student], f"You were removed from {project.title}", actor=request.user)
                m.delete()
                messages.success(request, f"Removed {m.student.display_name}.")
        elif action == "make_lead" and is_lead:
            m = get_object_or_404(project.memberships, pk=request.POST.get("membership"))
            project.memberships.update(is_lead=False)
            m.is_lead = True
            m.save(update_fields=["is_lead"])
            messages.success(request, f"{m.student.display_name} is now the team lead.")
        elif action == "leave" and project.is_member(request.user):
            m = project.memberships.get(student=request.user)
            if m.is_lead and project.memberships.count() > 1:
                messages.error(request, "Make someone else the lead before leaving.")
            else:
                m.delete()
                if not project.memberships.exists():
                    project.delete()
                    messages.info(request, "You left, and the empty project was removed.")
                else:
                    messages.info(request, f"You left {project.title}.")
                return redirect("core:dashboard")
        return redirect("projects:team", code=project.code)

    return render(request, "projects/team.html", {
        "project": project,
        "memberships": project.memberships.select_related("student").order_by("-is_lead", "joined_at"),
        "is_lead": is_lead,
        "max_team": settings.MAX_TEAM_SIZE,
        "join_url": request.build_absolute_uri(reverse("projects:join")),
    })


@login_required
@require_POST
def toggle_like(request, code):
    project = _project_for(request, code, "view")
    like, created = Like.objects.get_or_create(project=project, user=request.user)
    if not created:
        like.delete()
    elif not project.is_member(request.user):
        notify(project.members, f"{request.user.display_name} liked {project.title}",
               project.get_absolute_url(), actor=request.user)
    if _is_ajax(request):
        return JsonResponse({"active": created, "count": project.likes.count()})
    return redirect(request.POST.get("next") or project.get_absolute_url())


@login_required
@require_POST
def toggle_bookmark(request, code):
    project = _project_for(request, code, "view")
    bm, created = Bookmark.objects.get_or_create(project=project, user=request.user)
    if not created:
        bm.delete()
    if _is_ajax(request):
        return JsonResponse({"active": created})
    return redirect(request.POST.get("next") or project.get_absolute_url())


# ------------------------------------------------------- media & links -------

@login_required
@require_POST
def media_upload(request, code):
    project = _project_for(request, code, "edit")
    saved = 0
    for f in request.FILES.getlist("media"):
        ext = f.name.rsplit(".", 1)[-1].lower() if "." in f.name else ""
        if ext in IMAGE_EXTS:
            kind = MediaItem.Kind.IMAGE
        elif ext in VIDEO_EXTS:
            kind = MediaItem.Kind.VIDEO
        else:
            messages.error(request, f"{f.name}: only images ({', '.join(IMAGE_EXTS)}) and videos ({', '.join(VIDEO_EXTS)}) are allowed.")
            continue
        if f.size > 100 * 1024 * 1024:
            messages.error(request, f"{f.name} is over 100 MB.")
            continue
        MediaItem.objects.create(project=project, kind=kind, file=f, uploaded_by=request.user,
                                 caption=request.POST.get("caption", "")[:140], order=project.media.count())
        saved += 1
    if saved:
        messages.success(request, f"Added {saved} item{'s' if saved != 1 else ''} to the gallery.")
    if _is_ajax(request):
        return JsonResponse({"saved": saved, "redirect": project.get_absolute_url() + "#gallery"})
    return redirect(project.get_absolute_url() + "#gallery")


@login_required
@require_POST
def media_delete(request, code, pk):
    project = _project_for(request, code, "edit")
    item = get_object_or_404(project.media, pk=pk)
    item.file.delete(save=False)
    item.delete()
    messages.success(request, "Removed from the gallery.")
    return redirect(project.get_absolute_url() + "#gallery")


@login_required
@require_POST
def link_add(request, code):
    project = _project_for(request, code, "edit")
    form = LinkForm(request.POST)
    if form.is_valid():
        link = form.save(commit=False)
        link.project, link.added_by = project, request.user
        link.save()
        messages.success(request, "Link added.")
    else:
        messages.error(request, "Enter a title and a valid URL (starting with https://).")
    return redirect(project.get_absolute_url() + "#links")


@login_required
@require_POST
def link_delete(request, code, pk):
    project = _project_for(request, code, "edit")
    get_object_or_404(Link, project=project, pk=pk).delete()
    return redirect(project.get_absolute_url() + "#links")


# ---------------------------------------------------------------- vault ------

@login_required
def vault_browse(request, code):
    project = _project_for(request, code, "private")
    directory = vault.clean_path(request.GET.get("dir", ""))
    dirs, files = vault.browse(project, directory)
    readme = next((f for f in files if f.name.lower() in ("readme.md", "readme.txt", "readme")), None)
    all_latest = project.files.filter(is_latest=True)
    user = request.user
    show_flags = user.is_faculty
    return render(request, "projects/vault.html", {
        "project": project,
        "dirs": dirs,
        "files": files,
        "directory": directory,
        "crumbs": vault.breadcrumbs(directory),
        "readme": readme,
        "total_files": all_latest.count(),
        "total_size": sum(all_latest.values_list("size", flat=True)),
        "recent": project.files.select_related("uploaded_by").order_by("-uploaded_at")[:6],
        "can_edit": project.can_edit(user),
        "flags": vault.similarity_flags(project) if show_flags else None,
    })


@login_required
@require_POST
def vault_upload(request, code):
    project = _project_for(request, code, "edit")
    files = request.FILES.getlist("files")
    paths = request.POST.getlist("paths")
    base_dir = request.POST.get("dir", "")
    note = request.POST.get("note", "").strip()
    added = unchanged = 0
    errors = []
    for i, f in enumerate(files):
        relpath = paths[i] if i < len(paths) else ""
        try:
            a, u = vault.handle_upload(project, f, request.user, base_dir, note, relpath=relpath)
            added += a
            unchanged += u
        except vault.VaultError as exc:
            errors.append(str(exc))

    if added:
        project.save(update_fields=["updated_at"])
        notify(project.members, f"{request.user.display_name} uploaded {added} file{'s' if added != 1 else ''} to {project.title}",
               reverse("projects:vault", args=[project.code]), actor=request.user)
    summary = f"{added} file{'s' if added != 1 else ''} saved"
    if unchanged:
        summary += f", {unchanged} unchanged"
    for e in errors:
        messages.error(request, e)
    if added or unchanged:
        messages.success(request, summary + ".")
    target = reverse("projects:vault", args=[project.code]) + (f"?dir={base_dir}" if base_dir else "")
    if _is_ajax(request):
        return JsonResponse({"added": added, "unchanged": unchanged, "errors": errors, "redirect": target})
    return redirect(target)


def _vault_file(request, code, pk, need="private"):
    project = _project_for(request, code, need)
    return project, get_object_or_404(ProjectFile.objects.select_related("uploaded_by"), project=project, pk=pk)


@login_required
def vault_file(request, code, pk):
    project, pf = _vault_file(request, code, pk)
    user = request.user

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "comment" and request.POST.get("body", "").strip():
            line = request.POST.get("line", "")
            FileComment.objects.create(
                file=pf, author=user, body=request.POST["body"].strip(),
                line=int(line) if line.isdigit() else None,
            )
            where = f" (line {line})" if line.isdigit() else ""
            notify(project.members + [project.guide],
                   f"{user.display_name} commented on {pf.path}{where}",
                   reverse("projects:file", args=[project.code, pf.pk]) + "#comments",
                   actor=user, email=user.is_faculty)
            messages.success(request, "Comment posted.")
        elif action == "resolve":
            c = get_object_or_404(FileComment, pk=request.POST.get("comment"), file__project=project)
            if project.can_edit(user) or c.author == user:
                c.resolved = not c.resolved
                c.save(update_fields=["resolved"])
        return redirect(reverse("projects:file", args=[project.code, pf.pk]) + "#comments")

    history = list(pf.history().select_related("uploaded_by"))
    comments = list(FileComment.objects.filter(file__project=project, file__path=pf.path).select_related("author", "file"))
    parent_dir = pf.path.rsplit("/", 1)[0] if "/" in pf.path else ""

    diff = None
    previous = next((h for h in history if h.version < pf.version), None)
    if request.GET.get("compare") and previous and pf.is_text and previous.is_text:
        diff = []
        for line in difflib.unified_diff(previous.content.splitlines(), pf.content.splitlines(),
                                         f"v{previous.version}", f"v{pf.version}", lineterm="", n=3):
            kind = "meta" if line.startswith(("---", "+++", "@@")) else {"+": "add", "-": "del"}.get(line[:1], "ctx")
            diff.append((kind, line))

    lines = pf.content.split("\n") if pf.is_text and pf.line_count <= 8000 else None
    return render(request, "projects/file.html", {
        "project": project, "file": pf, "history": history, "comments": comments,
        "commented_lines": {c.line for c in comments if c.line and c.file_id == pf.id and not c.resolved},
        "lines": lines, "previous": previous, "diff": diff,
        "crumbs": vault.breadcrumbs(parent_dir), "can_edit": project.can_edit(user),
    })


@login_required
@xframe_options_sameorigin
def vault_raw(request, code, pk):
    _, pf = _vault_file(request, code, pk)
    ctype = mimetypes.guess_type(pf.name)[0] or "application/octet-stream"
    if ctype.startswith("text/html") or pf.extension in ("svg", "xml", "js"):
        ctype = "text/plain"  # never let uploaded markup run in our origin
    inline = request.GET.get("download") is None and (pf.is_image or pf.is_pdf)
    try:
        handle = pf.file.open("rb")
    except FileNotFoundError as exc:
        raise Http404 from exc
    resp = FileResponse(handle, content_type=ctype, as_attachment=not inline, filename=pf.name)
    resp["X-Content-Type-Options"] = "nosniff"
    return resp


@login_required
def vault_edit(request, code, pk):
    project, pf = _vault_file(request, code, pk, need="edit")
    if not pf.is_text:
        messages.error(request, "Only text files can be edited in the browser.")
        return redirect("projects:file", code=code, pk=pk)
    if request.method == "POST":
        content = request.POST.get("content", "").replace("\r\n", "\n")
        new, created = vault.add_file(project, pf.path, content.encode("utf-8"), request.user,
                                      request.POST.get("note", "").strip() or "Edited in browser")
        messages.success(request, f"Saved as version {new.version}." if created else "No changes to save.")
        return redirect("projects:file", code=code, pk=new.pk)
    return render(request, "projects/file_edit.html", {"project": project, "file": pf})


@login_required
def vault_new(request, code):
    project = _project_for(request, code, "edit")
    directory = vault.clean_path(request.GET.get("dir", ""))
    if request.method == "POST":
        path = vault.clean_path(request.POST.get("path", ""))
        if not path:
            messages.error(request, "Give the file a name.")
        elif project.files.filter(path=path, is_latest=True).exists():
            messages.error(request, f"{path} already exists.")
        else:
            content = request.POST.get("content", "").replace("\r\n", "\n")
            pf, _ = vault.add_file(project, path, content.encode("utf-8"), request.user, "Created in browser")
            return redirect("projects:file", code=code, pk=pf.pk)
    return render(request, "projects/file_edit.html", {"project": project, "file": None, "directory": directory})


@login_required
@require_POST
def vault_delete(request, code, pk):
    project, pf = _vault_file(request, code, pk, need="edit")
    versions = ProjectFile.objects.filter(project=project, path=pf.path)
    for v in versions:
        v.file.delete(save=False)
    versions.delete()
    messages.success(request, f"Deleted {pf.path} and its history.")
    parent = pf.path.rsplit("/", 1)[0] if "/" in pf.path else ""
    return redirect(reverse("projects:vault", args=[code]) + (f"?dir={parent}" if parent else ""))


@login_required
@require_POST
def vault_restore(request, code, pk):
    """Make an old version the latest again (as a new version)."""
    project, pf = _vault_file(request, code, pk, need="edit")
    with pf.file.open("rb") as fh:
        data = fh.read()
    new, created = vault.add_file(project, pf.path, data, request.user, f"Restored version {pf.version}")
    messages.success(request, f"Restored v{pf.version} as v{new.version}." if created else "That version is already the latest.")
    return redirect("projects:file", code=code, pk=new.pk)
