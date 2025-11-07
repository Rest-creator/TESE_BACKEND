# TESE Marketplace - Deployment Guide

## Table of Contents
1. [Deployment Overview](#deployment-overview)
2. [Environment Setup](#environment-setup)
3. [Local Development](#local-development)
4. [Production Deployment](#production-deployment)
5. [Database Migration](#database-migration)
6. [Environment Variables](#environment-variables)
7. [Monitoring & Maintenance](#monitoring--maintenance)

---

## Deployment Overview

### Deployment Environments

| Environment | Purpose | Database | Configuration |
|-------------|---------|----------|---------------|
| **Local** | Development | SQLite | DEBUG=True |
| **Staging** | Testing | PostgreSQL | DEBUG=True |
| **Production** | Live | PostgreSQL | DEBUG=False |

### Current Production Setup

- **Platform**: Sevalla (formerly Render)
- **URL**: https://tesebackend-4ic7p.sevalla.app
- **Server**: Gunicorn WSGI
- **Database**: PostgreSQL with pgvector
- **Redis**: Channel layer for WebSockets
- **CDN**: Bytescale for images

---

## Environment Setup

### Prerequisites

**Required Software:**
- Python 3.9+
- PostgreSQL 13+ (production)
- Redis 6+ (for WebSockets)
- Git

**Recommended Tools:**
- Virtual environment (venv/virtualenv)
- PostgreSQL GUI (pgAdmin, DBeaver)
- Redis GUI (RedisInsight)

### System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3-pip python3-dev postgresql postgresql-contrib redis-server
sudo apt install libpq-dev  # PostgreSQL adapter
```

**macOS:**
```bash
brew install python postgresql redis
```

**Windows:**
- Download Python from python.org
- Download PostgreSQL from postgresql.org
- Download Redis from redis.io (or use WSL)

---

## Local Development

### 1. Clone Repository

```bash
git clone <repository-url>
cd Tese-Marketplace/Backend
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Unix/macOS)
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Environment Variables

Create `.env` file in project root:

```env
# Django Settings
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (SQLite for development)
DATABASE_URL=sqlite:///db.sqlite3

# Bytescale
BYTESCALE_API_KEY=your-bytescale-api-key
BYTESCALE_ACCOUNT_ID=your-account-id

# Payment Gateways
STRIPE_SECRET_KEY=sk_test_your-stripe-key
PAYNOW_INTEGRATION_ID=your-paynow-id
PAYNOW_SECRET_KEY=your-paynow-secret

# URLs
PAYNOW_RETURN_URL=http://localhost:8000/paynow/return/
PAYNOW_RESULT_URL=http://localhost:8000/paynow/result/
```

### 5. Database Setup

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load initial data (optional)
python manage.py loaddata initial_categories.json
```

### 6. Run Development Server

```bash
# Start Django development server
python manage.py runserver

# Access at: http://localhost:8000
# Admin panel: http://localhost:8000/admin
```

### 7. Run Redis (for WebSockets)

```bash
# Start Redis server
redis-server

# Or on Windows with WSL
wsl redis-server
```

### 8. Run Channels Development Server (Optional)

```bash
# For WebSocket support
daphne -b 0.0.0.0 -p 8000 teseapp.asgi:application
```

---

## Production Deployment

### Option 1: Sevalla/Render Deployment

#### 1. Prepare Application

**Update settings for production:**

```python
# teseapp/settings.py

import os
import dj_database_url

DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = [
    'tesebackend-4ic7p.sevalla.app',
    'yourdomain.com',
]

# Database
DATABASES = {
    'default': dj_database_url.config(
        default='postgresql://user:password@host:5432/dbname',
        conn_max_age=600,
        ssl_require=True
    )
}

# Static files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
```

#### 2. Create `Procfile`

```procfile
web: gunicorn teseapp.wsgi:application --bind 0.0.0.0:$PORT --workers 3
```

#### 3. Create `runtime.txt`

```
python-3.9.18
```

#### 4. Update `requirements.txt`

```bash
pip freeze > requirements.txt
```

Make sure it includes:
- `gunicorn`
- `psycopg2-binary`
- `dj-database-url`
- `whitenoise` (for static files)

#### 5. Deploy to Sevalla

**Via Sevalla Dashboard:**
1. Create new Web Service
2. Connect GitHub repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `gunicorn teseapp.wsgi:application`
5. Add environment variables
6. Deploy

**Environment Variables to Set:**
```
DJANGO_SECRET_KEY=<generate-new-secret-key>
DEBUG=False
DATABASE_URL=<provided-by-sevalla>
REDIS_URL=<provided-by-sevalla>
BYTESCALE_API_KEY=<your-key>
STRIPE_SECRET_KEY=<your-key>
PAYNOW_INTEGRATION_ID=<your-id>
PAYNOW_SECRET_KEY=<your-key>
```

#### 6. Run Migrations

```bash
# SSH into Sevalla shell or use dashboard
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

---

### Option 2: Heroku Deployment

#### 1. Install Heroku CLI

```bash
# Install Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# Login
heroku login
```

#### 2. Create Heroku App

```bash
heroku create tese-marketplace-backend

# Add PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# Add Redis
heroku addons:create heroku-redis:hobby-dev
```

#### 3. Configure Environment

```bash
heroku config:set DJANGO_SECRET_KEY=your-secret-key
heroku config:set DEBUG=False
heroku config:set BYTESCALE_API_KEY=your-key
heroku config:set STRIPE_SECRET_KEY=your-key
```

#### 4. Deploy

```bash
git add .
git commit -m "Deploy to Heroku"
git push heroku main

# Run migrations
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
```

---

### Option 3: VPS Deployment (Ubuntu)

#### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install python3-pip python3-venv nginx postgresql redis-server

# Install pgvector extension
sudo apt install postgresql-13-pgvector
```

#### 2. PostgreSQL Setup

```bash
# Create database and user
sudo -u postgres psql

CREATE DATABASE tese_marketplace;
CREATE USER tese_user WITH PASSWORD 'secure_password';
ALTER ROLE tese_user SET client_encoding TO 'utf8';
ALTER ROLE tese_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE tese_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE tese_marketplace TO tese_user;

# Enable pgvector extension
\c tese_marketplace
CREATE EXTENSION vector;
\q
```

#### 3. Application Setup

```bash
# Clone repository
cd /var/www
sudo git clone <repository-url> tese-backend
cd tese-backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn

# Configure environment
sudo nano .env
# (Add all environment variables)

# Run migrations
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

#### 4. Gunicorn Setup

Create `gunicorn.service`:

```ini
[Unit]
Description=Gunicorn daemon for TESE Marketplace
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/tese-backend
Environment="PATH=/var/www/tese-backend/venv/bin"
ExecStart=/var/www/tese-backend/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/var/www/tese-backend/tese.sock \
    teseapp.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
```

#### 5. Nginx Configuration

Create `/etc/nginx/sites-available/tese-backend`:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias /var/www/tese-backend/staticfiles/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/tese-backend/tese.sock;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/tese-backend /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

#### 6. SSL Certificate (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

---

## Database Migration

### Development to Production

#### 1. Export Data from SQLite

```bash
python manage.py dumpdata --natural-foreign --natural-primary \
    -e contenttypes -e auth.Permission \
    --indent 4 > data_export.json
```

#### 2. Update Database Settings

```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'tese_marketplace',
        'USER': 'tese_user',
        'PASSWORD': 'secure_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

#### 3. Create PostgreSQL Schema

```bash
python manage.py migrate
```

#### 4. Import Data

```bash
python manage.py loaddata data_export.json
```

#### 5. Rebuild Search Index

```bash
python manage.py shell
```

```python
from django.apps import apps
from search.services.search_services import index_object

Listing = apps.get_model('teseapi', 'Listing')

for listing in Listing.objects.all():
    try:
        index_object(listing)
        print(f"Indexed listing {listing.id}")
    except Exception as e:
        print(f"Failed to index {listing.id}: {e}")
```

---

## Environment Variables

### Complete Environment Variable Reference

```env
# Django Core
DJANGO_SECRET_KEY=your-50-char-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Redis (for Channels)
REDIS_URL=redis://localhost:6379/0

# CDN & Storage
BYTESCALE_API_KEY=public_223k2Hc8KviJh2jj3gX3aSrz95ZX
BYTESCALE_ACCOUNT_ID=223k2Hc

# Payment Gateways
STRIPE_SECRET_KEY=sk_live_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

PAYNOW_INTEGRATION_ID=your_integration_id
PAYNOW_SECRET_KEY=your_paynow_secret_key
PAYNOW_RETURN_URL=https://yourdomain.com/paynow/return/
PAYNOW_RESULT_URL=https://yourdomain.com/paynow/result/

# Email (optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Twilio (optional)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
```

### Generating Secret Key

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

---

## Monitoring & Maintenance

### Logging

**Configure logging in `settings.py`:**

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'django.log',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### Database Backup

```bash
# Automated backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/tese-marketplace"

# PostgreSQL backup
pg_dump -U tese_user tese_marketplace > $BACKUP_DIR/db_$DATE.sql

# Compress
gzip $BACKUP_DIR/db_$DATE.sql

# Delete backups older than 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
```

### Health Check Endpoint

```python
# teseapi/views_app/health.py
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    try:
        # Check database
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return JsonResponse({
            'status': 'healthy',
            'database': 'connected'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=500)
```

### Performance Monitoring

```bash
# Install monitoring tools
pip install django-debug-toolbar  # Development only
pip install sentry-sdk  # Production error tracking
```

**Sentry Configuration:**

```python
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,
    send_default_pii=True
)
```

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Error

**Error:** `FATAL: password authentication failed`

**Solution:**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Reset password
sudo -u postgres psql
ALTER USER tese_user PASSWORD 'new_password';
```

#### 2. Redis Connection Error

**Error:** `Error 111 connecting to localhost:6379`

**Solution:**
```bash
# Start Redis
sudo systemctl start redis
sudo systemctl enable redis
```

#### 3. Static Files Not Loading

**Solution:**
```bash
python manage.py collectstatic --noinput
```

Check Nginx configuration for static files path.

#### 4. 502 Bad Gateway

**Solution:**
```bash
# Check Gunicorn is running
sudo systemctl status gunicorn

# Restart services
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

---

## Security Checklist

Before production deployment:

- [ ] `DEBUG = False`
- [ ] Strong `SECRET_KEY` generated
- [ ] `ALLOWED_HOSTS` configured
- [ ] SSL/HTTPS enabled
- [ ] Database credentials secured
- [ ] Environment variables not in code
- [ ] CORS properly configured
- [ ] Security headers enabled
- [ ] Regular backups scheduled
- [ ] Error tracking configured
- [ ] Admin panel secured (change URL)
- [ ] Rate limiting enabled
- [ ] SQL injection protection (ORM)
- [ ] XSS protection enabled

---

*Last Updated: 2024*
*Deployment Version: 1.0.0*
