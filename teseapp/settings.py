# teseapp/settings.py
from pathlib import Path
from datetime import timedelta
import os
from dotenv import load_dotenv
import dj_database_url

# Load local .env if present (harmless on Render, but not required)
load_dotenv()

# ----------------------
# BASE DIRECTORY
# ----------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# ----------------------
# SECURITY
# ----------------------
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "django-insecure-default-key")

# Allow overriding DEBUG via env var: set DJANGO_DEBUG to 'True' or 'False'
DEBUG = str(os.environ.get("DJANGO_DEBUG", "True")).lower() in ("1", "true", "yes")

ALLOWED_HOSTS = [
    "swapback.zchpc.ac.zw",
    "localhost",
    "127.0.0.1",
    "tesebackend-4ic7p.sevalla.app",
    "tese-backend-wq0d.onrender.com"
]

# ----------------------
# APPLICATION DEFINITION
# ----------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Your apps
    "teseapi",
    "pgvector.django",
    "search",
    'messaging.apps.MessagingConfig',
    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "channels",
]

# ----------------------
# MIDDLEWARE
# ----------------------
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",   # MUST BE FIRST
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ----------------------
# URLS / ASGI / WSGI
# ----------------------
ROOT_URLCONF = "teseapp.urls"
ASGI_APPLICATION = "teseapp.asgi.application"  # Channels support
WSGI_APPLICATION = "teseapp.wsgi.application"  # For gunicorn

# ----------------------
# TEMPLATES
# ----------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ----------------------
# DATABASES
# ----------------------
# Uses separate DB env vars. If you instead supply DATABASE_URL, you can switch to dj_database_url.parse(...)
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.postgresql",
#         "NAME": os.environ.get("DB_NAME", "tese"),
#         "USER": os.environ.get("DB_USER", "tese"),
#         "PASSWORD": os.environ.get("DB_PASSWORD", "bvldcmefwomk"),
#         "HOST": os.environ.get(
#             "DB_HOST",
#             "continental-gold-chinchilla-lpqnj-postgresql.continental-gold-chinchilla-lpqnj.svc.cluster.local",
#         ),
#         "PORT": os.environ.get("DB_PORT", "5432"),
#     }
# }
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set.")

DATABASES = {
    'default': dj_database_url.parse(
        DATABASE_URL,
        # This is critical for connecting to Render from your local machine
        ssl_require=True 
    )
}

# ----------------------
# AUTH USER
# ----------------------
AUTH_USER_MODEL = "teseapi.User"

# ----------------------
# PASSWORD VALIDATION
# ----------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ----------------------
# INTERNATIONALIZATION
# ----------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Harare"
USE_I18N = True
USE_TZ = True

# ----------------------
# STATIC FILES
# ----------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ----------------------
# CORS (allow your frontend domains)
# ----------------------

CORS_ALLOW_CREDENTIALS = True

# ----------------------
# REST FRAMEWORK (JWT only)
# ----------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ("rest_framework_simplejwt.authentication.JWTAuthentication",),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
}

# ----------------------
# SIMPLE JWT SETTINGS
# ----------------------
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
}

# ----------------------
# CHANNELS (optional)
# ----------------------
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(os.environ.get("REDIS_HOST", "127.0.0.1"), int(os.environ.get("REDIS_PORT", 6379)))],
        },
    }
}

# ----------------------
# HTTPS / Proxy Headers (if using reverse proxy)
# ----------------------
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ----------------------
# Bytescale Configuration
# ----------------------
BYTESCALE_API_KEY = os.environ.get("BYTESCALE_API_KEY", "public_223k2Hc8KviJh2jj3gX3aSrz95ZX")
BYTESCALE_ACCOUNT_ID = os.environ.get("BYTESCALE_ACCOUNT_ID", "223k2Hc")

# ----------------------
# Payment / External Keys
# ----------------------
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
PAYNOW_SECRET_KEY = os.environ.get("PAYNOW_SECRET_KEY")
PAYNOW_INTEGRATION_ID = os.environ.get("PAYNOW_INTEGRATION_ID")

# Optional URLs Paynow will redirect to after payment
PAYNOW_RETURN_URL = os.environ.get("PAYNOW_RETURN_URL", "https://yourdomain.com/paynow/return/")
PAYNOW_RESULT_URL = os.environ.get("PAYNOW_RESULT_URL", "https://yourdomain.com/paynow/result/")

# ----------------------
# Any additional settings below...
# ----------------------
# settings.py

CORS_ALLOWED_ORIGINS = [
    "https://tese-frontend.onrender.com",
    "http://localhost:8080",
]


