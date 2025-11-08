# Tese Marketplace: Deployment Guide

## Overview
This document outlines the deployment strategy and procedures for the Tese Marketplace, a full-stack application built with React (frontend) and Django (backend). The deployment leverages Sevalla's CI/CD platform for automated builds and deployments.

## Deployment Architecture

### Technology Stack
- **Frontend**: React.js
- **Backend**: Django (Python)
- **CI/CD Platform**: Sevalla
- **Version Control**: GitHub
- **Containerization**: Docker (managed by Sevalla)

### System Requirements
- Python 3.8+
- Node.js 14+
- PostgreSQL 12+
- Git

## CI/CD Pipeline with Sevalla

### Prerequisites
1. GitHub repository containing the project
2. Sevalla account with admin access
3. Required environment variables configured in Sevalla

### Automated Deployment Process

#### 1. Repository Integration
- Connect Sevalla to your GitHub repository
- Configure repository access permissions
- Set up webhooks for automatic deployment triggers

#### 2. Build Process
Sevalla automatically handles the following build steps:

**Frontend Build**
```bash
npm install
npm run build
```

**Backend Setup**
```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

#### 3. Deployment Configuration
Create a `sevalla.yml` configuration file in the project root:

```yaml
build:
  docker:
    web: Dockerfile
    worker: worker.Dockerfile  # if using background workers

env:
  - DJANGO_SETTINGS_MODULE=config.settings.production
  - DEBUG=0
  - SECRET_KEY=${SECRET_KEY}
  - DATABASE_URL=${DATABASE_URL}
  - ALLOWED_HOSTS=.sevalla.app

domains:
  - tese-marketplace.sevalla.app
```

## Critical Configuration

### requirements.txt Management
Ensure your `requirements.txt` is meticulously maintained:
- Pin all package versions explicitly
- Group dependencies logically
- Regularly update and test dependency updates

Example:
```
# Core
Django==4.2.0
djangorestframework==3.14.0

# Database
psycopg2-binary==2.9.6
dj-database-url==1.2.0

# Authentication
djangorestframework-simplejwt==5.2.2
dj-rest-auth==3.0.0

# CORS
corsheaders==3.14.0
```

### Environment Variables
Configure these essential environment variables in Sevalla:
- `SECRET_KEY`: Django secret key
- `DATABASE_URL`: PostgreSQL connection string
- `DEBUG`: Set to `0` in production
- `ALLOWED_HOSTS`: Configured domain(s)
- `CORS_ALLOWED_ORIGINS`: Frontend URLs
- `EMAIL_*`: Email configuration

## Alternative Deployment Options

### Render.com
1. Connect GitHub repository
2. Configure build command: `npm install && npm run build`
3. Set start command: `gunicorn config.wsgi`
4. Configure environment variables

### AWS (Manual Setup)
1. EC2 instance setup
2. Nginx + Gunicorn configuration
3. PostgreSQL RDS configuration
4. S3 for static/media files
5. Route 53 for DNS management

## Troubleshooting

### Common Issues
1. **Build Failures**
   - Check `requirements.txt` for version conflicts
   - Verify Python and Node.js version compatibility
   - Review build logs in Sevalla dashboard

2. **Database Connection Issues**
   - Verify `DATABASE_URL` format
   - Check database credentials and permissions
   - Ensure database server is accessible

3. **Static Files Not Loading**
   - Run `collectstatic` during build
   - Check `STATIC_URL` and `STATIC_ROOT` settings
   - Verify file permissions

## Maintenance

### Regular Tasks
- Monitor application logs
- Update dependencies regularly
- Backup database
- Review and rotate secrets/API keys

## Rollback Procedure
1. Navigate to Sevalla dashboard
2. Select the deployment
3. Choose "Rollback" option
4. Select previous stable version
5. Confirm rollback

## Security Considerations
- Enable HTTPS
- Implement rate limiting
- Regular security audits
- Keep dependencies updated
- Use environment variables for sensitive data

## Support
For deployment-related issues, contact:
- DevOps Team: devops@example.com
- Development Team: dev@example.com
