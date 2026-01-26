# Valorant Profile Generator

A Django web application for creating and displaying Valorant player profiles with a cyberpunk HUD aesthetic.

## Features

- **Input Form Page**: Dynamic form to input player information including:
  - In-game name and profile picture
  - Team name and logo
  - Multiple agents with images
  - Player roles with icons
  - Teammates with pictures
  - Up to 4 characteristic abilities (C, Q, E, X keys)
  - Player biography

- **Display Page**: Beautiful cyberpunk-themed profile display with:
  - Skewed containers with neon glows
  - Tactical HUD aesthetic
  - Agent showcase
  - Team roster with member avatars
  - Role badges
  - Special abilities grid
  - Responsive design

- **Profile List**: Browse all created profiles
- **SQLite Database**: Stores all profile data and image uploads

## Requirements

- Python 3.8+
- Django 4.2+
- Pillow (for image handling)

## Installation

1. **Navigate to the project directory:**
   ```powershell
   cd "c:\Users\Neko-Pc\Desktop\Biorni Projects Syncthing\Self Teaching\Tyloo Template\valorant_profile"
   ```

2. **Create a virtual environment:**
   ```powershell
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

4. **Install dependencies:**
   ```powershell
   pip install django pillow
   ```

5. **Run migrations to create the database:**
   ```powershell
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create a superuser (optional, for admin access):**
   ```powershell
   python manage.py createsuperuser
   ```

## Running the Application

1. **Start the development server:**
   ```powershell
   python manage.py runserver
   ```

2. **Open your browser and navigate to:**
   - Main page (profile list): `http://127.0.0.1:8000/`
   - Create profile: `http://127.0.0.1:8000/create/`
   - Admin panel: `http://127.0.0.1:8000/admin/`

## Usage

### Creating a Profile

1. Go to `http://127.0.0.1:8000/create/`
2. Fill in your basic information:
   - In-game name
   - Profile picture (upload)
   - Team name
   - Team logo (upload)
   - Bio (optional)

3. Add your agents:
   - Click "+ Add Agent"
   - Enter agent name
   - Upload agent picture
   - Repeat for multiple agents

4. Add your roles:
   - Click "+ Add Role"
   - Enter role name (e.g., Sentinel, Controller)
   - Upload role icon
   - Repeat for multiple roles

5. Add your teammates:
   - Click "+ Add Teammate"
   - Enter teammate name
   - Upload teammate picture
   - Repeat for all teammates

6. Add your abilities (max 4):
   - Click "+ Add Ability"
   - Select key binding (C, Q, E, or X)
   - Enter ability name
   - Enter ability description
   - Repeat for up to 4 abilities

7. Click "Create Profile" to save

### Viewing Profiles

- Browse all profiles at `http://127.0.0.1:8000/`
- Click "View Profile" on any profile card
- Navigate back using the "← Back to List" button

## Project Structure

```
valorant_profile/
├── manage.py
├── db.sqlite3 (created after migrations)
├── media/ (created for uploaded images)
├── valorant_profile/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
└── profiles/
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── forms.py
    ├── models.py
    ├── urls.py
    ├── views.py
    └── templates/
        └── profiles/
            ├── input_form.html
            ├── display_profile.html
            └── profile_list.html
```

## Models

- **Profile**: Main player profile (name, pictures, team, bio)
- **Agent**: Agents the player uses
- **Role**: Player roles (Duelist, Sentinel, etc.)
- **Teammate**: Team members
- **Ability**: Player characteristic abilities (C, Q, E, X)

## Database

The application uses SQLite database (`db.sqlite3`) which is created automatically when you run migrations. All uploaded images are stored in the `media/` directory.

## Admin Panel

Access the Django admin panel at `http://127.0.0.1:8000/admin/` to:
- Manage all profiles
- Edit agents, roles, teammates, and abilities
- View database entries

## Customization

### Changing Colors

Edit the CSS variables in the template files:
- `--color-accent-primary`: Primary accent color (default: #ff4655)
- `--color-accent-secondary`: Secondary accent color (default: #00f5ff)

### Modifying Layout

The display template uses CSS Grid with skewed transforms. You can modify the `.main-grid` and `.abilities-grid` classes to change the layout.

## Troubleshooting

**Images not displaying:**
- Make sure `MEDIA_URL` and `MEDIA_ROOT` are correctly set in `settings.py`
- Ensure the development server is serving media files
- Check that images were successfully uploaded to the `media/` directory

**Database errors:**
- Delete `db.sqlite3` and run migrations again
- Make sure you ran `python manage.py migrate`

**Form submission errors:**
- Ensure all required fields are filled
- Check that image files are in a supported format (JPG, PNG, GIF)
- Verify file sizes are reasonable (under 10MB)

## License

This project is for educational purposes.
