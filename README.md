# Valorant Profiles

A Django web app for managing and displaying Valorant player profiles, including agent selections, roles, maps, team affiliations, abilities, and player cards.

---

## Features

- Create, edit, and delete player profiles
- Select agents, roles, and preferred maps
- Assign players to teams
- Display a stylized player card
- Bio / description per profile
- Profile picture via upload or URL

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/bismalaja/valo_playercard.git
cd valo_playercard
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run locally

Runs migrations, seeds the database, and starts the dev server in one command:

```bash
honcho start dev
```

Or manually:

```bash
python manage.py migrate
python manage.py setup_project
python manage.py runserver
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000).

---

## Deployment (Heroku)

The `Procfile` handles migrations and seeding automatically on deploy:

```
web: python manage.py migrate && python manage.py setup_project && gunicorn valorant_profile.wsgi --log-file -
```

Set these config vars in production before first deploy:

```bash
SECRET_KEY=<strong-random-secret>
DEBUG=False
ALLOWED_HOSTS=valo-playercard.xyz,www.valo-playercard.xyz
CSRF_TRUSTED_ORIGINS=https://valo-playercard.xyz,https://www.valo-playercard.xyz
BOOTSTRAP_ADMIN_USERNAME=admin
BOOTSTRAP_ADMIN_EMAIL=admin@example.com
BOOTSTRAP_ADMIN_PASSWORD=<strong-admin-password>
```

`BOOTSTRAP_ADMIN_PASSWORD` is required for first-time admin bootstrap in production.
After the admin exists, startup continues even if it is not set.

---

## Static Images

Agent and role icons are stored locally under:

```
profiles/static/profiles/images/agents/
profiles/static/profiles/images/roles/
```

Map and team icons are loaded from external URLs defined in `setup_project.py`.

---

## Admin Bootstrap

`setup_project` can bootstrap a superuser using environment variables:

- `BOOTSTRAP_ADMIN_USERNAME`
- `BOOTSTRAP_ADMIN_EMAIL`
- `BOOTSTRAP_ADMIN_PASSWORD`

Password rotation is explicit:

```bash
python manage.py setup_project --rotate-admin-password
```
