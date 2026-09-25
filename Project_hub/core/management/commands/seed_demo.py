"""Fill the database with a small, realistic demo dataset.

    python manage.py seed_demo          # add demo data (refuses if users already exist)
    python manage.py seed_demo --reset  # wipe everything first
"""

import io
import random
import shutil
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont

from accounts.models import User
from evaluation.models import Criterion, Remark, ReviewRound, Rubric, Score
from mentoring.models import Milestone, ProgressLog
from notifications.models import Notification
from projects import vault
from projects.models import Bookmark, FileComment, Like, Link, MediaItem, Membership, Project

PASSWORD = "demo12345"
YEAR = timezone.localdate().year

STUDENTS = [
    ("Aarav", "Shah", "COMPS", "A", "12"), ("Diya", "Patel", "COMPS", "A", "27"),
    ("Kabir", "Nair", "COMPS", "B", "41"), ("Meera", "Joshi", "COMPS", "B", "08"),
    ("Rohan", "Kulkarni", "IT", "A", "15"), ("Ananya", "Deshpande", "IT", "A", "33"),
    ("Ishaan", "Verma", "IT", "B", "04"), ("Sara", "Fernandes", "AIDS", "A", "19"),
    ("Arjun", "Menon", "AIDS", "A", "22"), ("Nisha", "Reddy", "EXTC", "B", "30"),
    ("Vivaan", "Gupta", "EXTC", "B", "11"), ("Tara", "Pillai", "COMPS", "C", "36"),
    ("Kunal", "Bhatt", "IT", "C", "02"), ("Riya", "Chopra", "AIDS", "B", "17"),
]

PROJECTS = [
    {
        "title": "CampusEats", "tagline": "Pre-order canteen food and skip the lunch-hour queue.",
        "type": "MA", "sem": 1, "branch": "COMPS", "status": "building", "tech": "Django, React, SQLite, Razorpay",
        "abstract": "Long queues at the college canteen waste up to 20 minutes of every lunch break.\n\nCampusEats lets students browse the day's menu, pre-order and pay, and pick up when their token is called. Canteen staff get a live order board and end-of-day sales summary. We surveyed 180 students before building it; 74% said they would use pre-ordering at least twice a week.",
        "members": [0, 1, 2], "guide": 0, "tone_imgs": 3, "likes": 9,
    },
    {
        "title": "Sahayak: Sign Language Interpreter", "tagline": "Real-time Indian Sign Language to text using a webcam.",
        "type": "MA", "sem": 1, "branch": "AIDS", "status": "building", "tech": "Python, TensorFlow, MediaPipe, Flask",
        "abstract": "Sahayak recognises 40 common Indian Sign Language gestures from a normal laptop webcam and converts them to text and speech.\n\nHand landmarks are extracted with MediaPipe and classified by an LSTM trained on a dataset we recorded with 12 volunteers (≈9,000 clips). Current validation accuracy is 91%.",
        "members": [7, 8, 13], "guide": 1, "tone_imgs": 2, "likes": 14,
    },
    {
        "title": "Smart Irrigation Controller", "tagline": "Soil-moisture driven watering for small farms, on a ₹900 budget.",
        "type": "MA", "sem": 1, "branch": "EXTC", "status": "completed", "tech": "ESP32, C++, MQTT, Grafana",
        "abstract": "An ESP32 reads capacitive soil-moisture sensors and a rain sensor, and switches a relay-driven pump only when the soil actually needs water.\n\nReadings are published over MQTT to a small dashboard. In a two-week trial on a 0.5-acre plot the controller used 38% less water than the farmer's fixed timer.",
        "members": [9, 10], "guide": 1, "tone_imgs": 2, "likes": 6,
    },
    {
        "title": "LibTrack", "tagline": "The college library catalogue, with due-date reminders on WhatsApp.",
        "type": "MA", "sem": 1, "branch": "IT", "status": "planning", "tech": "Node.js, Express, PostgreSQL, Twilio",
        "abstract": "LibTrack digitises the issue/return register, lets students search the catalogue from their phones, and sends reminders two days before a book is due.",
        "members": [4, 5, 6], "guide": None, "tone_imgs": 1, "likes": 3,
    },
    {
        "title": "Attendance via Face Recognition", "tagline": "Take attendance for a 60-student class in under a minute.",
        "type": "MI", "sem": 1, "branch": "COMPS", "status": "completed", "tech": "Python, OpenCV, Tkinter, SQLite",
        "abstract": "A desktop app that captures a classroom photo, detects and recognises faces, and marks attendance in a local database with a CSV export for faculty.",
        "members": [3, 11], "guide": 0, "tone_imgs": 2, "likes": 11,
    },
    {
        "title": "Placement Prep Portal", "tagline": "Company-wise previous questions, mock tests and a senior-mentor board.",
        "type": "MI", "sem": 1, "branch": "IT", "status": "completed", "tech": "PHP, MySQL, Bootstrap",
        "abstract": "A portal where seniors post interview experiences and questions by company, and juniors take timed mock tests.",
        "members": [12], "guide": 0, "tone_imgs": 1, "likes": 5,
    },
]

TONES = [("#23407A", "#DCE4F2"), ("#8A3B25", "#F4DDD3"), ("#2F5D4A", "#D9EAE0"),
         ("#7A5C1E", "#F3E7C9"), ("#3E5566", "#DDE6EC"), ("#7E2D45", "#F2D9E0")]

SHARED_HELPER = """// Shared date helpers
export function formatDate(d) {
  const months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  return `${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}`;
}

export function daysBetween(a, b) {
  const ms = Math.abs(b.getTime() - a.getTime());
  return Math.round(ms / (1000 * 60 * 60 * 24));
}

export function isWeekend(d) {
  return d.getDay() === 0 || d.getDay() === 6;
}
"""


def mock_screenshot(title, tone, variant):
    """Draw a simple app-screenshot-like image so demo galleries aren't empty."""
    bg, fg = TONES[tone]
    w, h = 1280, 800
    img = Image.new("RGB", (w, h), "#F7F4EE")
    d = ImageDraw.Draw(img)
    try:
        font_big = ImageFont.truetype("arial.ttf", 38)
        font = ImageFont.truetype("arial.ttf", 22)
    except OSError:
        font_big = font = ImageFont.load_default()
    d.rectangle([0, 0, w, 70], fill=bg)
    d.text((32, 20), title, fill=fg, font=font)
    if variant == 0:
        d.rectangle([0, 70, 250, h], fill="#EDE7DC")
        for i in range(6):
            d.rounded_rectangle([24, 110 + i * 56, 226, 146 + i * 56], 8, fill="#FFFFFF" if i else fg)
        d.text((300, 110), "Dashboard", fill="#1B1A17", font=font_big)
        for i in range(3):
            x = 300 + i * 320
            d.rounded_rectangle([x, 180, x + 290, 330], 14, fill="#FFFFFF", outline="#E1D8C8", width=2)
            d.text((x + 24, 200), ["Orders today", "Avg. wait", "Revenue"][i], fill="#787165", font=font)
            d.text((x + 24, 250), ["128", "4 min", "₹9,420"][i], fill=bg, font=font_big)
        d.rounded_rectangle([300, 360, 1240, 760], 14, fill="#FFFFFF", outline="#E1D8C8", width=2)
        pts = [(340 + i * 85, 700 - random.randint(40, 280)) for i in range(11)]
        d.line(pts, fill=bg, width=5, joint="curve")
    elif variant == 1:
        for i in range(2):
            for j in range(3):
                x, y = 60 + j * 400, 120 + i * 330
                d.rounded_rectangle([x, y, x + 360, y + 290], 16, fill="#FFFFFF", outline="#E1D8C8", width=2)
                d.rounded_rectangle([x + 16, y + 16, x + 344, y + 170], 10, fill=fg)
                d.text((x + 20, y + 190), f"Item {i * 3 + j + 1}", fill="#1B1A17", font=font)
                d.rounded_rectangle([x + 20, y + 236, x + 150, y + 272], 8, fill=bg)
    else:
        d.rounded_rectangle([340, 150, 940, 690], 20, fill="#FFFFFF", outline="#E1D8C8", width=2)
        d.ellipse([560, 200, 720, 360], fill=fg, outline=bg, width=6)
        d.text((500, 400), "Recognised: HELLO", fill=bg, font=font_big)
        for i in range(4):
            d.rounded_rectangle([400, 480 + i * 45, 880, 510 + i * 45], 8, fill="#EDE7DC")
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return buf.getvalue()


class Command(BaseCommand):
    help = "Create demo users, projects, files, milestones and marks."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete all existing data first")

    def handle(self, *args, **opts):
        random.seed(7)
        if opts["reset"]:
            for model in [Notification, Score, Remark, ReviewRound, Criterion, Rubric, Project, User]:
                model.objects.all().delete()
            for folder in ["media", "private_media"]:
                shutil.rmtree(settings.BASE_DIR / folder, ignore_errors=True)
        elif User.objects.exists():
            raise CommandError("The database already has users. Run with --reset to replace everything with demo data.")

        admin = User.objects.create_superuser("admin", "admin@somaiya.edu", PASSWORD,
                                              first_name="Office", last_name="Admin", role=User.Role.ADMIN, is_staff=True)
        guides = [
            self._user("prof.mehta", "Anita", "Mehta", User.Role.GUIDE, designation="Associate Professor"),
            self._user("prof.rao", "Vikram", "Rao", User.Role.GUIDE, designation="Assistant Professor"),
        ]
        evaluator = self._user("dr.iyer", "Sunita", "Iyer", User.Role.EVALUATOR, designation="Professor & HoD")
        students = [
            self._user(f"{f.lower()}.{l.lower()}", f, l, User.Role.STUDENT, branch=b, division=dv, roll_no=r)
            for f, l, b, dv, r in STUDENTS
        ]

        projects = []
        for i, spec in enumerate(PROJECTS):
            p = Project.objects.create(
                title=spec["title"], tagline=spec["tagline"], abstract=spec["abstract"], tech_stack=spec["tech"],
                project_type=spec["type"], semester=spec["sem"], batch_year=YEAR, branch=spec["branch"],
                status=spec["status"], guide=guides[spec["guide"]] if spec["guide"] is not None else None,
                is_featured=i in (0, 1),
            )
            for n, idx in enumerate(spec["members"]):
                Membership.objects.create(project=p, student=students[idx], is_lead=n == 0)
            for v in range(spec["tone_imgs"]):
                MediaItem.objects.create(
                    project=p, kind=MediaItem.Kind.IMAGE, order=v, uploaded_by=students[spec["members"][0]],
                    caption=["Main dashboard", "Listing screen", "Detail view"][v],
                    file=ContentFile(mock_screenshot(p.title, p.tone, v if i != 1 else 2 - v), name=f"{p.code}-{v}.png"),
                )
            fans = [s for s in students if s.id not in {students[k].id for k in spec["members"]}]
            for s in random.sample(fans, min(spec["likes"], len(fans))):
                Like.objects.create(project=p, user=s)
            if p.guide:
                Milestone.create_defaults(p)
            projects.append(p)

        self._vault(projects, students)
        self._mentoring(projects, guides, students)
        self._evaluation(projects, admin, evaluator, guides)

        for s in students[:6]:
            Bookmark.objects.create(project=projects[1], user=s)
        Link.objects.create(project=projects[1], title="MediaPipe Hands paper", url="https://arxiv.org/abs/2006.10214", added_by=students[7])
        Link.objects.create(project=projects[0], title="Survey results (Google Form)", url="https://forms.google.com/", added_by=students[0])

        eats = projects[0]
        views_file = eats.files.get(path="orders/views.py", is_latest=True)
        for text, url, actor, who in [
            ("Anita Mehta commented on orders/views.py (line 11)", f"/projects/{eats.code}/vault/{views_file.pk}/#comments", guides[0], students[:3]),
            ("“Synopsis” approved", f"/mentoring/{eats.code}/", guides[0], students[:3]),
            ("Diya Patel uploaded 1 file to CampusEats", f"/projects/{eats.code}/vault/", students[1], [students[0], students[2]]),
            ("CampusEats submitted “Design review” for review", f"/mentoring/{eats.code}/", students[0], [guides[0]]),
            ("Results for “Mini project final viva” are out", "/evaluation/", admin, [students[3], students[11], students[12]]),
        ]:
            Notification.objects.bulk_create([Notification(recipient=r, actor=actor, text=text, url=url) for r in who])

        self.stdout.write(self.style.SUCCESS("\nDemo data ready. Every account uses the password: " + PASSWORD))
        self.stdout.write("  admin         -> admin (Insights, People, rounds)")
        self.stdout.write("  guide         -> prof.mehta, prof.rao")
        self.stdout.write("  evaluator     -> dr.iyer")
        self.stdout.write("  students      -> aarav.shah (CampusEats lead), sara.fernandes, nisha.reddy ...")

    # ------------------------------------------------------------------ helpers
    def _user(self, username, first, last, role, **extra):
        u = User(username=username, first_name=first, last_name=last, role=role,
                 email=f"{username}@somaiya.edu", **extra)
        u.set_password(PASSWORD)
        u.save()
        return u

    def _vault(self, projects, students):
        eats, sahayak, irrigation, libtrack, attendance, _ = projects
        lead = students[0]
        files = {
            "README.md": "# CampusEats\n\nPre-order canteen food and skip the queue.\n\n## Run locally\n\n```bash\npip install -r requirements.txt\npython manage.py migrate\npython manage.py runserver\n```\n\n## Team\n- Aarav Shah (backend)\n- Diya Patel (frontend)\n- Kabir Nair (payments)\n",
            "requirements.txt": "Django>=4.2\ndjangorestframework\nrazorpay\n",
            "orders/models.py": 'from django.db import models\n\n\nclass MenuItem(models.Model):\n    name = models.CharField(max_length=80)\n    price = models.DecimalField(max_digits=6, decimal_places=2)\n    available = models.BooleanField(default=True)\n\n    def __str__(self):\n        return self.name\n\n\nclass Order(models.Model):\n    STATUS = [("placed", "Placed"), ("ready", "Ready"), ("collected", "Collected")]\n\n    student = models.ForeignKey("auth.User", on_delete=models.CASCADE)\n    items = models.ManyToManyField(MenuItem, through="OrderLine")\n    token = models.PositiveIntegerField()\n    status = models.CharField(max_length=10, choices=STATUS, default="placed")\n    created_at = models.DateTimeField(auto_now_add=True)\n\n    @property\n    def total(self):\n        return sum(line.item.price * line.qty for line in self.lines.all())\n\n\nclass OrderLine(models.Model):\n    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="lines")\n    item = models.ForeignKey(MenuItem, on_delete=models.PROTECT)\n    qty = models.PositiveSmallIntegerField(default=1)\n',
            "orders/views.py": 'from django.shortcuts import get_object_or_404, redirect, render\n\nfrom .models import MenuItem, Order\n\n\ndef menu(request):\n    items = MenuItem.objects.filter(available=True)\n    return render(request, "orders/menu.html", {"items": items})\n\n\ndef next_token():\n    last = Order.objects.order_by("-token").first()\n    return (last.token + 1) if last else 1\n\n\ndef place_order(request):\n    order = Order.objects.create(student=request.user, token=next_token())\n    return redirect("orders:status", order.pk)\n',
            "frontend/src/App.jsx": 'import { useEffect, useState } from "react";\nimport { formatDate } from "./utils/dates";\n\nexport default function App() {\n  const [menu, setMenu] = useState([]);\n\n  useEffect(() => {\n    fetch("/api/menu/").then((r) => r.json()).then(setMenu);\n  }, []);\n\n  return (\n    <main>\n      <h1>Today\'s menu · {formatDate(new Date())}</h1>\n      <ul>\n        {menu.map((item) => (\n          <li key={item.id}>{item.name} — ₹{item.price}</li>\n        ))}\n      </ul>\n    </main>\n  );\n}\n',
            "frontend/src/utils/dates.js": SHARED_HELPER,
        }
        for path, text in files.items():
            vault.add_file(eats, path, text.encode(), lead, "Initial upload")
        vault.add_file(eats, "orders/views.py", (files["orders/views.py"] + '\n\ndef order_status(request, pk):\n    order = get_object_or_404(Order, pk=pk, student=request.user)\n    return render(request, "orders/status.html", {"order": order})\n').encode(),
                       students[1], "Added order status page")
        # Same helper in another group's vault -> shows up as a similarity flag
        vault.add_file(libtrack, "src/utils/dates.js", SHARED_HELPER.encode(), students[4], "Initial upload")
        vault.add_file(libtrack, "src/server.js", b'const express = require("express");\nconst app = express();\n\napp.get("/api/books", async (req, res) => {\n  res.json([]);\n});\n\napp.listen(3000);\n', students[4])

        vault.add_file(sahayak, "README.md", b"# Sahayak\n\nIndian Sign Language to text.\n\n1. `pip install -r requirements.txt`\n2. `python app.py`\n", students[7])
        vault.add_file(sahayak, "model/train.py", b'import numpy as np\nimport tensorflow as tf\n\nSEQ_LEN = 30\nNUM_CLASSES = 40\n\n\ndef build_model():\n    model = tf.keras.Sequential([\n        tf.keras.layers.LSTM(64, return_sequences=True, input_shape=(SEQ_LEN, 126)),\n        tf.keras.layers.LSTM(128),\n        tf.keras.layers.Dense(64, activation="relu"),\n        tf.keras.layers.Dense(NUM_CLASSES, activation="softmax"),\n    ])\n    model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])\n    return model\n\n\nif __name__ == "__main__":\n    X, y = np.load("data/X.npy"), np.load("data/y.npy")\n    build_model().fit(X, y, epochs=60, validation_split=0.15)\n', students[8])
        vault.add_file(irrigation, "firmware/main.cpp", b'#include <WiFi.h>\n#include <PubSubClient.h>\n\nconst int SOIL_PIN = 34;\nconst int PUMP_PIN = 26;\nconst int DRY_THRESHOLD = 2300;\n\nvoid setup() {\n  pinMode(PUMP_PIN, OUTPUT);\n  Serial.begin(115200);\n}\n\nvoid loop() {\n  int moisture = analogRead(SOIL_PIN);\n  digitalWrite(PUMP_PIN, moisture > DRY_THRESHOLD ? HIGH : LOW);\n  delay(5000);\n}\n', students[9])
        vault.add_file(attendance, "attendance.py", b'import cv2\nimport face_recognition\n\n\ndef mark_attendance(photo_path, known):\n    image = face_recognition.load_image_file(photo_path)\n    present = set()\n    for enc in face_recognition.face_encodings(image):\n        matches = face_recognition.compare_faces(list(known.values()), enc, tolerance=0.5)\n        for name, ok in zip(known, matches):\n            if ok:\n                present.add(name)\n    return present\n', students[3])

        views = eats.files.get(path="orders/views.py", is_latest=True)
        FileComment.objects.create(file=views, author=eats.guide, line=11,
                                   body="Two orders placed at the same moment could get the same token here. Consider select_for_update() or a database sequence.")
        FileComment.objects.create(file=views, author=students[0], body="Good catch, we'll fix it before the mid-term demo.")

    def _mentoring(self, projects, guides, students):
        today = timezone.localdate()
        for p in projects:
            ms = list(p.milestones.all())
            if not ms:
                continue
            for i, m in enumerate(ms):
                m.due_date = today + timedelta(days=-40 + i * 28)
            if p.status == Project.Status.COMPLETED:
                for m in ms:
                    m.status, m.submitted_at, m.reviewed_at = Milestone.Status.APPROVED, timezone.now(), timezone.now()
                    m.feedback = "Well done."
            else:
                ms[0].status = Milestone.Status.APPROVED
                ms[0].submission_note = "Synopsis PDF is in the vault under docs/. We interviewed the canteen manager and 180 students."
                ms[0].submitted_at = timezone.now() - timedelta(days=35)
                ms[0].feedback = "Clear problem statement. Narrow the scope for sem 1 to ordering + token board."
                ms[0].reviewed_at = timezone.now() - timedelta(days=33)
                ms[1].status = Milestone.Status.SUBMITTED
                ms[1].submission_note = "ER diagram and API list uploaded. Wireframes are in the gallery."
                ms[1].submitted_at = timezone.now() - timedelta(days=2)
            for m in ms:
                m.save()
            members = p.members
            ProgressLog.objects.create(project=p, author=p.guide, meeting_date=today - timedelta(days=14),
                                       summary="Reviewed the synopsis and discussed the database design.",
                                       next_steps="Finalise the ER diagram; set up the repo structure in the vault.")
            ProgressLog.objects.create(project=p, author=members[0], meeting_date=today - timedelta(days=5),
                                       summary="Finished the core models and first API endpoints. Frontend has the menu page working with dummy data.",
                                       next_steps="Hook the frontend to the real API; start on payments.")

    def _evaluation(self, projects, admin, evaluator, guides):
        rubric = Rubric.objects.create(name="Standard project rubric", created_by=admin,
                                       description="Used for mid-term and final reviews.")
        crit = [
            Criterion.objects.create(rubric=rubric, name="Problem understanding", max_marks=10, order=0),
            Criterion.objects.create(rubric=rubric, name="Implementation", max_marks=20, order=1),
            Criterion.objects.create(rubric=rubric, name="Presentation", max_marks=10, order=2),
            Criterion.objects.create(rubric=rubric, name="Report & documentation", max_marks=10, order=3),
        ]
        final_mini = ReviewRound.objects.create(
            name="Mini project final viva", rubric=rubric, project_type="MI", semester=1, batch_year=YEAR,
            review_date=timezone.localdate() - timedelta(days=10), state=ReviewRound.State.LOCKED,
            results_published=True, created_by=admin,
        )
        mid_major = ReviewRound.objects.create(
            name="Major project mid-semester review", rubric=rubric, project_type="MA", semester=1, batch_year=YEAR,
            review_date=timezone.localdate() + timedelta(days=6), created_by=admin,
        )
        for p in final_mini.projects():
            for s in p.members:
                for c in crit:
                    Score.objects.create(round=final_mini, project=p, student=s, criterion=c, marked_by=evaluator,
                                         marks=Decimal(random.randint(int(c.max_marks * .6), int(c.max_marks))))
            Remark.objects.create(round=final_mini, project=p, author=evaluator,
                                  text="Solid working demo. The report needs a proper testing section.")
        # Partially mark one major project so progress bars have something to show
        eats = projects[0]
        for s in eats.members[:2]:
            for c in crit:
                Score.objects.create(round=mid_major, project=eats, student=s, criterion=c, marked_by=evaluator,
                                     marks=Decimal(random.randint(int(c.max_marks * .55), int(c.max_marks * .9))))
