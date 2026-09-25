"""Code-vault helpers: storing uploads as versioned files and browsing them."""

import posixpath
import zipfile

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction

from .models import ProjectFile

SKIP_PARTS = {"__MACOSX", ".git", "node_modules", "__pycache__", ".venv", "venv", ".idea", ".vscode", ".DS_Store"}
MAX_FILE_BYTES = 20 * 1024 * 1024
MAX_ZIP_ENTRIES = 800
# Identical files smaller than this are too generic to flag as copied.
MIN_SIMILARITY_BYTES = 300


class VaultError(ValueError):
    pass


def clean_path(path):
    """Normalise a user-supplied path to a safe relative POSIX path, or '' if invalid."""
    path = (path or "").replace("\\", "/").strip().strip("/")
    path = posixpath.normpath(path) if path else ""
    if path in ("", ".") or path.startswith("..") or "/../" in f"/{path}/":
        return ""
    return path


def decode_text(data):
    if len(data) > settings.MAX_INLINE_CODE_BYTES or b"\x00" in data[:8192]:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin-1")


@transaction.atomic
def add_file(project, path, data, user, note=""):
    """Store `data` at `path`. Returns (ProjectFile, created) — created is False if unchanged."""
    path = clean_path(path)
    if not path:
        raise VaultError("Invalid file path.")
    if len(data) > MAX_FILE_BYTES:
        raise VaultError(f"{path} is larger than {MAX_FILE_BYTES // (1024 * 1024)} MB.")

    digest = ProjectFile.hash_bytes(data)
    previous = ProjectFile.objects.filter(project=project, path=path, is_latest=True).first()
    if previous and previous.sha256 == digest:
        return previous, False

    version = 1
    if previous:
        version = previous.version + 1
        previous.is_latest = False
        previous.save(update_fields=["is_latest"])

    pf = ProjectFile(
        project=project, path=path, content=decode_text(data), size=len(data),
        sha256=digest, version=version, note=note[:160], uploaded_by=user,
    )
    pf.file.save(posixpath.basename(path), ContentFile(data), save=False)
    pf.save()
    return pf, True


def _zip_members(zf):
    infos = [i for i in zf.infolist() if not i.is_dir()]
    infos = [i for i in infos if not (set(i.filename.replace("\\", "/").split("/")) & SKIP_PARTS)]
    if len(infos) > MAX_ZIP_ENTRIES:
        raise VaultError(f"That zip has more than {MAX_ZIP_ENTRIES} files. Remove build folders and try again.")
    names = [i.filename.replace("\\", "/") for i in infos]
    # If everything sits inside one top-level folder, drop that folder.
    tops = {n.split("/", 1)[0] for n in names}
    strip = len(tops) == 1 and all("/" in n for n in names)
    for info, name in zip(infos, names):
        yield info, (name.split("/", 1)[1] if strip else name)


def handle_upload(project, uploaded, user, base_dir="", note="", relpath="", extract_zip=True):
    """Store one uploaded file (or every file inside a zip). Returns (added, unchanged) counts.

    `relpath` is the file's path within a dropped folder; Django strips folders from
    upload names, so the browser sends it separately.
    """
    base_dir = clean_path(base_dir)
    added = unchanged = 0

    if relpath and set(clean_path(relpath).split("/")) & SKIP_PARTS:
        return 0, 0

    if extract_zip and uploaded.name.lower().endswith(".zip"):
        try:
            zf = zipfile.ZipFile(uploaded)
        except zipfile.BadZipFile as exc:
            raise VaultError("That zip file looks damaged.") from exc
        with zf:
            for info, name in _zip_members(zf):
                if info.file_size > MAX_FILE_BYTES:
                    continue
                _, created = add_file(project, posixpath.join(base_dir, name), zf.read(info), user, note)
                added += created
                unchanged += not created
        return added, unchanged

    name = clean_path(relpath) or uploaded.name
    _, created = add_file(project, posixpath.join(base_dir, name), uploaded.read(), user, note)
    return int(created), int(not created)


def browse(project, directory=""):
    """Return (subdirectories, files) directly inside `directory` for the latest versions."""
    directory = clean_path(directory)
    prefix = f"{directory}/" if directory else ""
    dirs, files = {}, []
    latest = project.files.filter(is_latest=True, path__startswith=prefix).order_by("path")
    for pf in latest:
        rest = pf.path[len(prefix):]
        if "/" in rest:
            top = rest.split("/", 1)[0]
            dirs.setdefault(top, {"name": top, "path": prefix + top, "count": 0})
            dirs[top]["count"] += 1
        else:
            files.append(pf)
    return sorted(dirs.values(), key=lambda d: d["name"].lower()), files


def breadcrumbs(directory):
    parts = clean_path(directory).split("/") if clean_path(directory) else []
    return [{"name": p, "path": "/".join(parts[: i + 1])} for i, p in enumerate(parts)]


def similarity_flags(project):
    """Latest files in `project` that are byte-identical to a latest file in another project."""
    mine = project.files.filter(is_latest=True, size__gte=MIN_SIMILARITY_BYTES).exclude(sha256="")
    by_hash = {f.sha256: f for f in mine}
    if not by_hash:
        return []
    matches = (
        ProjectFile.objects.filter(is_latest=True, sha256__in=by_hash.keys())
        .exclude(project=project)
        .select_related("project")
    )
    flags = {}
    for other in matches:
        own = by_hash[other.sha256]
        flags.setdefault(own.id, {"file": own, "others": []})["others"].append(other)
    return sorted(flags.values(), key=lambda f: f["file"].path)
