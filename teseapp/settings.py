# teseapp/settings.py

from pathlib import Path
from datetime import timedelta
import os
from dotenv import load_dotenv
load_dotenv()


# ----------------------
# BASE DIRECTORY
# ----------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# ----------------------
# SECURITY
# ----------------------
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "django-insecure-default-key")
DEBUG = True  # Set to False in production
ALLOWED_HOSTS = ["swapback.zchpc.ac.zw", "localhost", "127.0.0.1", "tesebackend-4ic7p.sevalla.app"]

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
    "modules.messaging",  # Messaging module
    "pgvector",
    "search",

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
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ----------------------
# URLS
# ----------------------
ROOT_URLCONF = "teseapp.urls"
ASGI_APPLICATION = "teseapp.asgi.application"  # Channels support

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


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='tese'),
        'USER': env('DB_USER', default='tese'),
        'PASSWORD': env('DB_PASSWORD', default='bvldcmefwomk'),
        'HOST': env('DB_HOST', default='continental-gold-chinchilla-lpqnj-postgresql.continental-gold-chinchilla-lpqnj.svc.cluster.local'),
        'PORT': env('DB_PORT', default='5432'),
    }
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
CORS_ALLOWED_ORIGINS = [
    "https://tese-dvx.pages.dev",
    "https://swapback.zchpc.ac.zw",
    "http://localhost:8080",
    "http://localhost:8081",
]
CORS_ALLOW_CREDENTIALS = False  # Not needed; JWT is stateless

# ----------------------
# REST FRAMEWORK (JWT only)
# ----------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
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
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}

# ----------------------
# HTTPS / Proxy Headers (if using reverse proxy)
# ----------------------
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')



# Bytescale Configuration
BYTESCALE_API_KEY = os.environ.get('BYTESCALE_API_KEY', 'public_223k2Hc8KviJh2jj3gX3aSrz95ZX')
BYTESCALE_ACCOUNT_ID = os.environ.get('BYTESCALE_ACCOUNT_ID', '223k2Hc')


import os

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
PAYNOW_SECRET_KEY = os.environ.get("PAYNOW_SECRET_KEY")

PAYNOW_INTEGRATION_ID = os.environ.get("PAYNOW_INTEGRATION_ID")
PAYNOW_SECRET_KEY = os.environ.get("PAYNOW_SECRET_KEY")


# Optional URLs Paynow will redirect to after payment
PAYNOW_RETURN_URL = os.environ.get("PAYNOW_RETURN_URL", "https://yourdomain.com/paynow/return/")
PAYNOW_RESULT_URL = os.environ.get("PAYNOW_RESULT_URL", "https://yourdomain.com/paynow/result/")


# settings.py
# replace `myproject` with the name of the folder that contains wsgi.py
WSGI_APPLICATION = "teseapp.wsgi.application"