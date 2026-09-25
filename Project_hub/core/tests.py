import io
import shutil
import tempfile
import zipfile
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from accounts.models import User
from evaluation.models import Criterion, ReviewRound, Rubric, Score
from projects import vault
from projects.models import Membership, Project, private_storage


def make_user(username, role=User.Role.STUDENT, **extra):
    u = User(username=username, email=f"{username}@somaiya.edu", role=role, first_name=username.title(), **extra)
    u.set_password("pw-12345678")
    u.save()
    return u


class ProjectHubTests(TestCase):
    def setUp(self):
        # Keep test uploads out of the real private_media folder
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        for attr in ("location", "base_location"):
            patcher = mock.patch.object(private_storage, attr, tmp)
            patcher.start()
            self.addCleanup(patcher.stop)

        self.lead = make_user("lead", branch="COMPS", division="A", roll_no="1")
        self.mate = make_user("mate")
        self.outsider = make_user("outsider")
        self.guide = make_user("guide", User.Role.GUIDE)
        self.evaluator = make_user("evaluator", User.Role.EVALUATOR)
        self.project = Project.objects.create(title="Demo", project_type="MA", semester=1, batch_year=2026, branch="COMPS")
        Membership.objects.create(project=self.project, student=self.lead, is_lead=True)
        self.file, _ = vault.add_file(self.project, "src/app.py", b"print('hi')\n", self.lead)

    def login(self, user):
        self.client.login(username=user.username, password="pw-12345678")

    def test_group_code_is_generated(self):
        self.assertEqual(self.project.code, "MA1-26-COMPS-01")
        second = Project.objects.create(title="Two", project_type="MA", semester=1, batch_year=2026, branch="COMPS")
        self.assertEqual(second.code, "MA1-26-COMPS-02")

    def test_vault_is_private(self):
        vault_url = f"/projects/{self.project.code}/vault/"
        raw_url = f"/projects/{self.project.code}/vault/{self.file.pk}/raw/"
        self.login(self.outsider)
        self.assertEqual(self.client.get(vault_url).status_code, 403)
        self.assertEqual(self.client.get(raw_url).status_code, 403)
        self.assertEqual(self.client.get(self.project.get_absolute_url()).status_code, 200)  # showcase is public
        for user in (self.lead, self.evaluator):
            self.login(user)
            self.assertEqual(self.client.get(vault_url).status_code, 200)

    def test_guide_sees_only_own_groups_private_pages(self):
        self.login(self.guide)
        self.assertEqual(self.client.get(f"/projects/{self.project.code}/vault/").status_code, 403)
        self.project.guide = self.guide
        self.project.save()
        self.assertEqual(self.client.get(f"/projects/{self.project.code}/vault/").status_code, 200)

    def test_reupload_creates_version_and_skips_unchanged(self):
        same, created = vault.add_file(self.project, "src/app.py", b"print('hi')\n", self.lead)
        self.assertFalse(created)
        v2, created = vault.add_file(self.project, "src/app.py", b"print('bye')\n", self.lead)
        self.assertTrue(created)
        self.assertEqual(v2.version, 2)
        self.assertEqual(self.project.files.filter(path="src/app.py", is_latest=True).count(), 1)

    def test_zip_upload_strips_top_folder_and_junk(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("demo/main.py", "x = 1\n")
            z.writestr("demo/node_modules/lib.js", "junk")
        upload = SimpleUploadedFile("code.zip", buf.getvalue())
        added, _ = vault.handle_upload(self.project, upload, self.lead)
        self.assertEqual(added, 1)
        self.assertTrue(self.project.files.filter(path="main.py").exists())

    def test_clean_path_blocks_traversal(self):
        self.assertEqual(vault.clean_path("../../etc/passwd"), "")
        self.assertEqual(vault.clean_path("a/../../b"), "")
        self.assertEqual(vault.clean_path("\\src\\app.py"), "src/app.py")

    def test_join_with_invite_code(self):
        self.login(self.mate)
        resp = self.client.post("/projects/join/", {"invite_code": self.project.invite_code.lower()})
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(self.project.is_member(self.mate))

    @override_settings(ALLOWED_EMAIL_DOMAIN="somaiya.edu")
    def test_register_requires_college_email(self):
        data = {"first_name": "A", "last_name": "B", "username": "newbie", "email": "a@gmail.com", "branch": "IT",
                "division": "A", "roll_no": "3", "password1": "Xy7!pass-word", "password2": "Xy7!pass-word"}
        self.assertEqual(self.client.post("/accounts/register/", data).status_code, 200)
        data["email"] = "a@somaiya.edu"
        self.assertEqual(self.client.post("/accounts/register/", data).status_code, 302)

    def test_marking_validates_range_and_locking(self):
        rubric = Rubric.objects.create(name="R")
        crit = Criterion.objects.create(rubric=rubric, name="Impl", max_marks=10)
        rnd = ReviewRound.objects.create(name="Mid", rubric=rubric, project_type="MA", semester=1, batch_year=2026)
        url = f"/evaluation/rounds/{rnd.pk}/mark/{self.project.code}/"
        self.login(self.evaluator)
        self.client.post(url, {f"m_{self.lead.id}_{crit.id}": "12"})
        self.assertFalse(Score.objects.exists())
        self.client.post(url, {f"m_{self.lead.id}_{crit.id}": "8.5"})
        self.assertEqual(Score.objects.get().marks, 8.5)
        rnd.state = ReviewRound.State.LOCKED
        rnd.save()
        self.assertEqual(self.client.post(url, {f"m_{self.lead.id}_{crit.id}": "9"}).status_code, 403)
        # students can't see the marking sheet at all
        self.login(self.lead)
        self.assertEqual(self.client.get(f"/evaluation/rounds/{rnd.pk}/").status_code, 403)

    def test_excel_export(self):
        rubric = Rubric.objects.create(name="R")
        Criterion.objects.create(rubric=rubric, name="Impl", max_marks=10)
        rnd = ReviewRound.objects.create(name="Mid", rubric=rubric, project_type="MA", semester=1, batch_year=2026)
        self.login(self.evaluator)
        resp = self.client.get(f"/evaluation/rounds/{rnd.pk}/export/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("spreadsheetml", resp["Content-Type"])
