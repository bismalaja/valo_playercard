"""
ASGI config for valorant_profile project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'valorant_profile.settings')

application = get_asgi_application()
