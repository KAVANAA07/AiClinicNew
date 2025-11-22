import os
from pathlib import Path
# import dj_database_url # No longer needed for local
import sys

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
try:
    from decouple import config, Config, RepositoryEnv
    # Explicitly specify the .env file path
    env_path = BASE_DIR / '.env'
    if env_path.exists():
        config = Config(RepositoryEnv(str(env_path)))
    else:
        config = Config()
except ImportError:
    # Fallback if python-decouple is not installed
    def config(key, default=None, cast=str):
        return os.environ.get(key, default)

# --- 1. CORE LOCAL DEVELOPMENT SETTINGS ---
SECRET_KEY = config('SECRET_KEY', 'django-insecure-=+c$c$j4z!0d9v$j1w!5a)0i=d!o(l!&!1v(l3x(e&n&n7z_d3')

# DEBUG should always be True for local development
DEBUG = True

# Allow localhost, 127.0.0.1, and your ngrok hostname (without https://)
ALLOWED_HOSTS = [
    '0a490259b696.ngrok-free.app',
    'b2ee8587838a.ngrok-free.app', # Add both URLs
    'localhost',
    '127.0.0.1'
]

INSTALLED_APPS = [
    # 'whitenoise.runserver_nostatic', # Removed - Not needed for standard local dev
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_q',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # 'whitenoise.middleware.WhiteNoiseMiddleware', # Removed - Not needed for local dev
    'corsheaders.middleware.CorsMiddleware', # Keep CorsMiddleware near the top
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'clinic_token_system.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'clinic_token_system.wsgi.application'


# --- 2. DATABASE CONFIGURATION (Simplified for Local SQLite) ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3', # Use the default SQLite file name
    }
}
# Removed dj_database_url and the 'RENDER' check


AUTH_PASSWORD_VALIDATORS = [
    { 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata' 
USE_I18N = True
USE_TZ = True

# --- 3. STATIC FILES CONFIGURATION (Simplified for Local Dev) ---
STATIC_URL = '/static/'
# STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles') # Removed - Not needed for local dev
# STORAGES = { # Removed - Not needed for local dev
#     "staticfiles": {
#         "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
#     },
# }

# You might need this if you have static files directly in your 'api' app
# STATICFILES_DIRS = [
#     os.path.join(BASE_DIR, 'api/static'), # Example if you have static files there
# ]


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- LOGGING CONFIGURATION ---
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
    'loggers': {
        'django.server': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'api': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# --- 4. CORS Configuration ---
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000", # Allow your React frontend
]
# Removed the CORS_FRONTEND_URL logic as it's not needed locally
CORS_ALLOW_CREDENTIALS = True


# --- 5. SMS/IVR CONFIGURATION (Dummy Keys for Simulation) ---
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', 'ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', 'your_auth_token')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', '+15005550006')

# --- AI / Summarization Backend Configuration ---
# Choose the AI backend. Options:
#  - 'local' : use a locally-loaded Hugging Face pipeline (requires transformers + torch installed)
#  - 'hf'    : use Hugging Face Inference API (recommended if you don't want to host weights locally)
#  - 'openai': use OpenAI-compatible API (optional)
# AI backend selection
AI_BACKEND = config('AI_BACKEND', 'hf')

# Hugging Face Inference API settings (only used when AI_BACKEND == 'hf')
# Example HF_INFERENCE_API_URL: https://api-inference.huggingface.co/models/sshleifer/distilbart-cnn-12-6
HF_INFERENCE_API_URL = config('HF_INFERENCE_API_URL', '')
# Your Hugging Face API token (keep secret; do NOT commit to source control)
HF_API_TOKEN = config('HF_API_TOKEN', '')

# OpenAI settings (only used when AI_BACKEND == 'openai')
OPENAI_API_KEY = config('OPENAI_API_KEY', '')
OPENAI_MODEL = config('OPENAI_MODEL', 'gpt-3.5-turbo')

# --- 6. DJANGO-Q SETTINGS ---
Q_CLUSTER = {
    'name': 'clinic-q-local',
    'workers': 2,
    'timeout': 90,
    'retry': 120,
    'queue_limit': 50,
    'catch_up': False,
    'orm': 'default',  # Use Django ORM instead of Redis
}