"""
WSGI config for valorant_profile project.
"""

import os

from django.core.wsgi import get_wsgi_application
from django.core.management import call_command

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'valorant_profile.settings')

# Attempt to migrate the database on startup
# This ensures tables exist even if the start command doesn't run migrate explicitly
try:
    print("--- STARTING MIGRATIONS FROM WSGI ---")
    call_command('migrate', interactive=False)
    print("--- MIGRATIONS FINISHED ---")
except Exception as e:
    print(f"--- MIGRATION FAILED: {e} ---")

application = get_wsgi_application()
