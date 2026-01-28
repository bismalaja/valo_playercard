"""
WSGI config for valorant_profile project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'valorant_profile.settings')

application = get_wsgi_application()
