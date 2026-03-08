# Copilot Instructions

## Project Overview

Django web app for managing Valorant player profiles — agent selections, roles, teams, maps, abilities, and a Pillow-generated player card image. Single Django app (`profiles`) within the `valorant_profile` project.

---

## Developer Workflows

**Start dev server (preferred):**
```bash
honcho start dev
```
This runs migrate + setup_project + runserver in one step.

**Manual equivalent:**
```bash
python manage.py migrate
python manage.py setup_project   # seeds all reference data + default superuser (admin/admin)
python manage.py runserver
```

**Re-seeding reference data** (agents, roles, maps, teams): re-run `setup_project`. It uses `update_or_create` — safe to run repeatedly.

---

## Architecture

### App Structure
All logic lives in `profiles/`. `valorant_profile/` is just configuration (settings, root URLs, wsgi).

### Model Layers
1. **Reference data** (admin-managed, seeded by `setup_project`): `Role`, `Agent`, `Team`, `Map`, `AbilityTemplate`
2. **Auth extension**: `UserProfile` — OneToOne with Django's `User`, stores `riot_id` + `riot_tag`
3. **Player data**: `Profile` (main entity), `Ability` (up to 4 per profile, keyed to `AbilityTemplate`)

### Profile Ownership (Claimed/Unclaimed)
`Profile.user` is nullable. A `null` user means the profile is an **unclaimed legacy profile**. The `is_claimed` property (`Profile.user is not None`) drives UI and permission checks. Claiming requires the user's `UserProfile.riot_id` + `riot_tag` to match the profile's stored credentials exactly (case-insensitive).

### Image Handling Pattern
Every media model has **two image fields**: an `ImageField` (upload) and a `URLField` (`_url` suffix). Always access images via the `get_icon_url()` method — it checks if the uploaded file physically exists before returning its URL, and falls back to the URL field. Static assets use paths like `/static/profiles/images/agents/Jett.png`.

### Storage Backend
- Local filesystem (`MEDIA_ROOT`) — uploaded media files are always stored locally

---

## Key Patterns

### Adding a New Agent/Map/Team/Role
Add the entry to the relevant list in `profiles/management/commands/setup_project.py` and drop the icon PNG into `profiles/static/profiles/images/<category>/`. Run `setup_project` to seed.

### Ability System
Exactly 4 ability slots (C, Q, E, X) defined by `AbilityTemplate` objects. Each `Ability` is linked to a profile + template with a `unique_together` constraint. The `get_ability_rows()` helper (in `views.py`) merges templates with existing saved abilities for form rendering.

### Riot ID Format
Tag must match `^#[a-zA-Z0-9]{2,5}$` (e.g. `#NA1`). This validator is defined identically on `UserProfile.riot_tag`, `Profile.riot_tag`, and `SignUpForm` — keep them in sync when changing.

### Card Image Generation
`profiles/utils/card_image.py` uses Pillow to composite a 1920×1080 PNG server-side. The `_load_image_from_url_or_path()` helper resolves `/static/...`, `/media/...`, absolute `https://` URLs, and bare filesystem paths in that order.

---

## External Dependencies & Deployment

- **Deployment target**: `https://valo-playercard.xyz` — `CSRF_TRUSTED_ORIGINS` is hardcoded in settings
- **Static files**: WhiteNoise serves statics in production; `collectstatic` must run before deploy
- **Procfile**: `web: python manage.py migrate && python manage.py setup_project && gunicorn valorant_profile.wsgi`
- **No test suite** is currently present in the project

---

## Key Files
- [`profiles/models.py`](profiles/models.py) — all data models
- [`profiles/views.py`](profiles/views.py) — all views including auth, claim/unclaim, CRUD
- [`profiles/utils/card_image.py`](profiles/utils/card_image.py) — Pillow card compositor
- [`profiles/management/commands/setup_project.py`](profiles/management/commands/setup_project.py) — reference data seed + superuser
- [`valorant_profile/settings.py`](valorant_profile/settings.py) — storage backend, CSRF config
