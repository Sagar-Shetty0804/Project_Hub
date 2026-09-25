# ProjectHub

A college project platform: students keep their code in a **private vault**, show photos and demo videos on a **public showcase**, and guides and evaluators **review, comment and mark** in the same place. No spreadsheets.

Built with Django and SQLite as a small prototype.

## Features

**Students**
- Create a project (a group code like `MA1-26-COMPS-01` is generated), then share a six-character invite code with teammates
- Private code vault: upload files, a whole folder or a `.zip`. Folder structure is kept, re-uploads become new versions, and any old version can be restored
- Syntax-highlighted code viewer, in-browser editor and "changes vs previous version" diff
- Showcase page with gallery (lightbox), demo videos, tech tags and links, visible to the whole college
- Milestones: submit work for your guide's review
- See published marks per criterion; download a completion certificate (PDF) when the project is completed
- Explore, like and save other projects

**Guides**
- Adopt groups that don't have a guide yet (default milestones are created automatically)
- Review milestone submissions (approve or request changes), set due dates
- Line-by-line comments on code; the team is notified
- Progress log / meeting notes
- "Identical file" hint when a file matches another group's file byte-for-byte

**Evaluators & admin**
- Rubrics with any criteria and max marks
- Review rounds for a batch of projects (type, semester, year, optional branch)
- Per-student marking sheet with live totals and validation; group remarks
- Lock rounds, publish results to students, export marks to Excel
- Insights dashboard, faculty account management, featured projects
- One-page project report (PDF)

Also: in-app notifications (optional email), dark mode, and a mobile layout.

## Run it

```bash
cd Project_hub
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo      # optional: demo users, projects, files and marks
python manage.py runserver
```

Open http://127.0.0.1:8000.

### Demo accounts (after `seed_demo`)

Every account uses the password `demo12345`.

| Role | Username |
|---|---|
| Admin | `admin` |
| Guide | `prof.mehta`, `prof.rao` |
| Evaluator | `dr.iyer` |
| Student | `aarav.shah` (CampusEats lead), `sara.fernandes`, `meera.joshi` (has published marks and a certificate) |

`python manage.py seed_demo --reset` wipes everything and recreates the demo data.

### Configuration

Copy `Project_hub/.env.example` to `Project_hub/.env` to change settings:

- `ALLOWED_EMAIL_DOMAIN`: only this email domain can register (default `somaiya.edu`; leave blank to allow any)
- `MAX_TEAM_SIZE`: default 4
- `EMAIL_NOTIFICATIONS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`: send real emails. Without them, emails are printed to the console.

Students register themselves. Guide, evaluator and admin accounts are created by an admin under **People**.

## Project layout

```
Project_hub/
  accounts/       custom User model with roles, login/register, settings, people
  projects/       projects, team, showcase media, links, likes, the code vault
  mentoring/      milestones and progress logs (guide workspace)
  evaluation/     rubrics, review rounds, scores, Excel export
  notifications/  in-app notifications
  core/           landing, dashboards, insights, PDFs, seed_demo command, tests
  templates/      all templates (one shared design system)
  static/         app.css and app.js (no front-end framework)
```

Vault files are stored in `Project_hub/private_media/`, outside the public media folder, and are only served through a view that checks permissions.

## Tests

```bash
cd Project_hub
python manage.py test core
```
