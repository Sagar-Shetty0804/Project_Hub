"""PDF generation (ReportLab): completion certificates and one-page project reports."""

from io import BytesIO

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

INK = colors.HexColor("#1B1A17")
MUTED = colors.HexColor("#6B665C")
ACCENT = colors.HexColor("#23407A")
LINE = colors.HexColor("#DDD6C8")
PAPER = colors.HexColor("#FBF8F2")


def certificate(project, student, results):
    buf = BytesIO()
    w, h = landscape(A4)
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(buf, pagesize=(w, h))
    c.setTitle(f"Certificate - {student.display_name}")

    c.setFillColor(PAPER)
    c.rect(0, 0, w, h, fill=1, stroke=0)
    # Double rule border
    c.setStrokeColor(ACCENT)
    c.setLineWidth(2.2)
    c.rect(14 * mm, 14 * mm, w - 28 * mm, h - 28 * mm)
    c.setLineWidth(0.6)
    c.rect(17 * mm, 17 * mm, w - 34 * mm, h - 34 * mm)

    c.setFillColor(ACCENT)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(w / 2, h - 38 * mm, "P R O J E C T H U B")
    c.setFillColor(INK)
    c.setFont("Times-Bold", 34)
    c.drawCentredString(w / 2, h - 56 * mm, "Certificate of Completion")

    c.setFont("Times-Italic", 14)
    c.setFillColor(MUTED)
    c.drawCentredString(w / 2, h - 72 * mm, "This is to certify that")
    c.setFillColor(INK)
    c.setFont("Times-Bold", 28)
    c.drawCentredString(w / 2, h - 88 * mm, student.display_name)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.8)
    c.line(w / 2 - 70 * mm, h - 92 * mm, w / 2 + 70 * mm, h - 92 * mm)

    c.setFont("Helvetica", 11)
    c.setFillColor(MUTED)
    sub = " · ".join(x for x in [student.class_label, project.get_branch_display()] if x)
    c.drawCentredString(w / 2, h - 99 * mm, sub)

    c.setFont("Times-Roman", 14)
    c.setFillColor(INK)
    c.drawCentredString(w / 2, h - 114 * mm, f"has successfully completed the {project.get_project_type_display().lower()}")
    c.setFont("Times-Bold", 18)
    c.drawCentredString(w / 2, h - 125 * mm, f"“{project.title}”")
    c.setFont("Times-Roman", 12)
    c.setFillColor(MUTED)
    c.drawCentredString(w / 2, h - 134 * mm, f"Semester {project.semester}, {project.batch_year}  ·  Group {project.code}")

    if results:
        total = sum(r["total"] for r in results)
        out_of = sum(r["out_of"] for r in results)
        c.setFont("Helvetica", 10)
        c.drawCentredString(w / 2, h - 144 * mm, f"Evaluated across {len(results)} review round(s): {total:g} / {out_of:g} marks")

    # Signature lines
    y = 36 * mm
    c.setStrokeColor(INK)
    c.setLineWidth(0.5)
    for x, label, name in [
        (w * 0.25, "Project Guide", project.guide.display_name if project.guide else ""),
        (w * 0.75, "Head of Department", ""),
    ]:
        c.line(x - 35 * mm, y, x + 35 * mm, y)
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(x, y - 6 * mm, label)
        if name:
            c.setFont("Times-Italic", 13)
            c.drawCentredString(x, y + 3 * mm, name)
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8)
    c.drawCentredString(w / 2, 22 * mm, f"Issued {timezone.localdate():%d %B %Y} · Verify with group code {project.code}")

    c.showPage()
    c.save()
    return buf.getvalue()


def project_report(project, milestones, results_by_student):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=18 * mm, bottomMargin=18 * mm, title=f"{project.title} - Report")
    eyebrow = ParagraphStyle("eyebrow", fontName="Helvetica-Bold", fontSize=8, textColor=ACCENT, spaceAfter=4, leading=10)
    title = ParagraphStyle("title", fontName="Times-Bold", fontSize=24, leading=28, textColor=INK, spaceAfter=4)
    tag = ParagraphStyle("tag", fontName="Times-Italic", fontSize=12, leading=16, textColor=MUTED, spaceAfter=10)
    h2 = ParagraphStyle("h2", fontName="Times-Bold", fontSize=14, leading=18, textColor=INK, spaceBefore=12, spaceAfter=6)
    body = ParagraphStyle("body", fontName="Helvetica", fontSize=9.5, leading=14, textColor=INK)
    small = ParagraphStyle("small", parent=body, fontSize=8, textColor=MUTED, alignment=TA_CENTER)

    def esc(s):
        return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def table(data, widths):
        t = Table(data, colWidths=widths, hAlign="LEFT")
        t.setStyle(TableStyle([
            ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8.5),
            ("FONT", (0, 1), (-1, -1), "Helvetica", 9),
            ("TEXTCOLOR", (0, 0), (-1, 0), MUTED),
            ("LINEBELOW", (0, 0), (-1, 0), 0.8, INK),
            ("LINEBELOW", (0, 1), (-1, -1), 0.3, LINE),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        return t

    story = [
        Paragraph(f"PROJECT REPORT · {esc(project.code)}", eyebrow),
        Paragraph(esc(project.title), title),
        Paragraph(esc(project.tagline), tag) if project.tagline else Spacer(1, 6),
    ]
    facts = [
        ["Type", project.period_label],
        ["Branch", project.get_branch_display()],
        ["Guide", project.guide.display_name if project.guide else "Not assigned"],
        ["Status", project.get_status_display()],
        ["Tech stack", ", ".join(project.tags) or "-"],
    ]
    ft = Table(facts, colWidths=[30 * mm, 140 * mm], hAlign="LEFT")
    ft.setStyle(TableStyle([
        ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 8.5), ("TEXTCOLOR", (0, 0), (0, -1), MUTED),
        ("FONT", (1, 0), (1, -1), "Helvetica", 9.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story += [ft, Paragraph("Abstract", h2), Paragraph(esc(project.abstract).replace("\n", "<br/>") or "-", body)]

    story.append(Paragraph("Team", h2))
    team = [["Name", "Class", "Email", "Marks (published)"]]
    for m in project.members:
        res = results_by_student.get(m.id, [])
        marks = ", ".join(f"{r['total']:g}/{r['out_of']:g}" for r in res) or "-"
        team.append([m.display_name, m.class_label, m.email, marks])
    story.append(table(team, [45 * mm, 32 * mm, 58 * mm, 39 * mm]))

    if milestones:
        story.append(Paragraph("Milestones", h2))
        ms = [["Milestone", "Due", "Status"]]
        for m in milestones:
            ms.append([m.title, m.due_date.strftime("%d %b %Y") if m.due_date else "-", m.get_status_display()])
        story.append(table(ms, [90 * mm, 35 * mm, 49 * mm]))

    story += [Spacer(1, 18), Paragraph(f"Generated by ProjectHub on {timezone.localdate():%d %B %Y}", small)]
    doc.build(story)
    return buf.getvalue()
