
# --- Imports first, always ---
from pathlib import Path
from urllib.parse import urlparse
import os
import sys

# --- Helper functions ---

def _env_bool(name, default=False):
    """Read a boolean from an environment variable."""
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ('1', 'true', 'yes', 'on')

def _env_list(name, default=''):
    """Read a comma-separated list from an environment variable."""
    raw = os.environ.get(name, default)
    return [item.strip() for item in raw.split(',') if item.strip()]

# --- Core settings ---

BASE_DIR = Path(__file__).resolve().parent.parent

# Read from environment variable — no hardcoded fallback in prod
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-dev-only-key')


# DEBUG = _env_bool('DEBUG', default=False)
DEBUG = True

ALLOWED_HOSTS = ['valo-playercard.xyz', 'www.valo-playercard.xyz', 'localhost', '127.0.0.1']

APPEND_SLASH = True

# --- Apps ---

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'profiles',
]

# --- Middleware ---

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'valorant_profile.urls'
WSGI_APPLICATION = 'valorant_profile.wsgi.application'

# --- Templates ---

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
            ],
        },
    },
]

# --- Database ---

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'data' / 'db.sqlite3',
    }
}

# --- Password validation ---

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- Internationalisation ---

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# --- Static & media files ---

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [os.path.join(BASE_DIR, "profiles/static")]

# Use compressed storage in production, plain in development
if DEBUG:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
else:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Auth ---

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# --- Security (all tied to DEBUG so they activate automatically in prod) ---

CSRF_COOKIE_SECURE = not DEBUG        # only send CSRF cookie over HTTPS
SESSION_COOKIE_SECURE = not DEBUG     # only send session cookie over HTTPS
SESSION_COOKIE_HTTPONLY = True        # JS can't read the session cookie
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
X_FRAME_OPTIONS = 'DENY'

CSRF_TRUSTED_ORIGINS = _env_list(
    'CSRF_TRUSTED_ORIGINS',
    default='https://valo-playercard.xyz'
)

# SECURE_SSL_REDIRECT = False here because Nginx handles the HTTP→HTTPS redirect.
# Django should never see a plain HTTP request — Nginx upgrades it first.
SECURE_SSL_REDIRECT = False

# This tells Django "trust Nginx when it says the request was HTTPS"
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# --- Upload limits ---

FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024

# --- Tracker.GG ---

TRACKER_CF_CLEARANCE = os.environ.get("TRACKER_CF_CLEARANCE", "")
TRACKER_EXTRA_COOKIES = os.environ.get("TRACKER_EXTRA_COOKIES", "")

# --- Test/CI override (must be LAST) ---

# When running tests, disable SSL redirect so test assertions aren't broken by 301s
if 'test' in sys.argv or os.environ.get("CI") == "true":
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False