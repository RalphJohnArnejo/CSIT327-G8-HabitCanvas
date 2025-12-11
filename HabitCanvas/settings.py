"""
Django settings for HabitCanvas project.
"""

from pathlib import Path
import os
# import dj_database_url
# from dotenv import load_dotenv

# Load environment variables from .env (for local development)
# load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent


# --------------------------
# SECURITY & DEBUG SETTINGS
# --------------------------

# SECRET_KEY should come from Render Environment Variables
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

# DEBUG is False in production, True only on local machine
DEBUG = True # os.getenv("DEBUG", "False").lower() == "true"

# Allow all hosts — Render URL included
ALLOWED_HOSTS = ['*']


# --------------------------
# APPLICATIONS
# --------------------------

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'main',
]


# --------------------------
# MIDDLEWARE
# --------------------------

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ✅ REQUIRED FOR RENDER STATIC FILES
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# --------------------------
# URL / WSGI CONFIG
# --------------------------

ROOT_URLCONF = 'HabitCanvas.urls'
WSGI_APPLICATION = 'HabitCanvas.wsgi.application'


# --------------------------
# TEMPLATES
# --------------------------

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / "main" / "templates",
            BASE_DIR / "main" / "templates" / "registration",
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# --------------------------
# DATABASE (Local = SQLite, Render = PostgreSQL)
# --------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# --------------------------
# PASSWORD VALIDATION
# --------------------------

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
    {'NAME': 'main.validators.CustomPasswordValidator'},
]


# --------------------------
# INTERNATIONALIZATION
# --------------------------

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Manila'
USE_I18N = True
USE_TZ = True


# --------------------------
# STATIC FILES (REQUIRED FOR RENDER)
# --------------------------

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "main" / "static"]  # assets inside your app
STATIC_ROOT = BASE_DIR / "staticfiles"  # folder Render will collect static files into

# WhiteNoise: compress & cache static files
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


# --------------------------
# AUTH REDIRECTS
# --------------------------

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'


# --------------------------
# DEFAULT PRIMARY KEY
# --------------------------

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
