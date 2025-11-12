# 🚀 Quick Production Deployment Checklist

## 🔴 CRITICAL - Must Complete Before Production

### 1. Database Migration (SQLite → PostgreSQL)
**Why:** SQLite can't handle multiple concurrent writes. With 5+ users writing simultaneously, you'll get database locks and errors.

**Steps:**
```bash
# Install PostgreSQL locally
# Download from: https://www.postgresql.org/download/windows/

# Install Python PostgreSQL adapter
pip install psycopg2-binary

# Update settings.py DATABASES section to:
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'drillreport',
        'USER': 'postgres',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Migrate data
python manage.py dumpdata > backup.json
# Change database settings
python manage.py migrate
python manage.py loaddata backup.json
```

**Test:** Have 5+ users create shifts at the same time. Should work smoothly.

---

### 2. Secure SECRET_KEY
**Why:** Exposed secret key allows attackers to forge sessions, bypass security.

**Steps:**
```bash
# Install python-decouple
pip install python-decouple

# Create .env file (copy from .env.example)
# Generate new secret key in Python:
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Add to .env file:
SECRET_KEY=<paste-generated-key-here>
```

**Update settings.py:**
```python
from decouple import config

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')
```

---

### 3. Disable DEBUG Mode
**Why:** DEBUG=True exposes sensitive information (database queries, file paths, settings).

**In .env file:**
```
DEBUG=False
```

**Add custom error pages:**
Create templates: `templates/404.html`, `templates/500.html`

---

### 4. Configure ALLOWED_HOSTS
**Why:** Django blocks requests from unknown hosts.

**In .env file:**
```
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,your-server-ip
```

---

### 5. Setup Automated Backups
**Why:** Protect against data loss (hardware failure, human error, ransomware).

**Daily backup script (backup.bat):**
```batch
@echo off
set BACKUP_DIR=C:\Backups\DailyDrillReport
set DATE=%date:~-4,4%%date:~-10,2%%date:~-7,2%

mkdir %BACKUP_DIR%\%DATE%

REM Backup database
pg_dump -U postgres drillreport > %BACKUP_DIR%\%DATE%\database.sql

REM Backup media files
xcopy /E /I C:\Users\PC\DailyDrillReport\media %BACKUP_DIR%\%DATE%\media

REM Keep only last 30 days
forfiles /P %BACKUP_DIR% /M * /D -30 /C "cmd /c if @isdir==TRUE rmdir /S /Q @path"
```

**Schedule with Task Scheduler:**
- Run daily at 2 AM
- Store backups on different drive/cloud

---

## 🟡 IMPORTANT - Recommended Before Production

### 6. Setup Real Email Backend
**Current:** Emails print to console (not sent).

**Steps:**
```bash
pip install django-anymail  # For SendGrid, Mailgun, etc.
```

**In .env:**
```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-company@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

**Update settings.py:**
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT', cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')
```

---

### 7. Add Error Logging
**Why:** Track errors, debug issues without DEBUG=True.

**Update settings.py:**
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django_errors.log',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        }
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}

ADMINS = [('Your Name', 'admin@yourdomain.com')]
```

**Create logs directory:**
```bash
mkdir logs
```

---

### 8. Setup HTTPS (SSL Certificate)
**Why:** Encrypt data in transit, required for modern browsers.

**Options:**
- **Free:** Let's Encrypt (free SSL certificate)
- **Paid:** Purchase from Certificate Authority

**Force HTTPS in settings.py:**
```python
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
```

---

### 9. Add Rate Limiting
**Why:** Prevent abuse, brute force attacks.

```bash
pip install django-ratelimit
```

**In views.py:**
```python
from django_ratelimit.decorators import ratelimit

@ratelimit(key='user', rate='5/m', method='POST')
def shift_create(request):
    # ... existing code
```

---

### 10. Setup Monitoring
**Why:** Get alerts when site goes down, track performance.

**Options:**
- **Free:** UptimeRobot (monitors site availability)
- **Paid:** Sentry (error tracking), New Relic (performance)

---

## 📊 Testing Checklist

Before going live, test with real users:

- [ ] 5+ users create shifts simultaneously (test database concurrency)
- [ ] Upload 50+ drilling progress entries per shift (test performance)
- [ ] Create 100+ shifts (test pagination, search)
- [ ] Test on slow internet connection (mobile data)
- [ ] Test client approval workflow with 3+ clients
- [ ] Test password reset email delivery
- [ ] Test backup/restore procedure
- [ ] Load test with 20+ concurrent users (use Apache JMeter or Locust)

---

## 🎯 Deployment Options

### Option A: Self-Hosted (Windows Server)
**Pros:** Full control, one-time cost  
**Cons:** You manage updates, security, backups

**Requirements:**
- Windows Server 2019/2022
- IIS with HTTP Platform Handler
- PostgreSQL 15+
- 4GB RAM minimum
- Daily backups

### Option B: Cloud Hosting (Recommended)
**Pros:** Automatic backups, scaling, security updates  
**Cons:** Monthly cost

**Options:**
1. **DigitalOcean App Platform** - $12/month
2. **Railway.app** - ~$10/month (PostgreSQL included)
3. **Heroku** - ~$16/month
4. **Azure App Service** - ~$55/month (enterprise)

### Option C: Hybrid (Database in cloud, app on-premises)
**Best of both worlds:**
- App runs on your server (full control)
- Database in cloud (ElephantSQL, Supabase - ~$10/month)
- Automatic database backups
- Better performance with concurrent users

---

## 🚀 Quick Start (Pilot Phase)

**Keep SQLite for now IF:**
- ✅ Less than 5 concurrent users
- ✅ Users take turns entering data (not simultaneously)
- ✅ Testing/pilot phase only (1-3 months)

**But still do these 3 things TODAY:**

1. **Secure your SECRET_KEY** (Steps 1-2 above)
2. **Setup daily backups** (Step 5)
3. **Set DEBUG=False when deployed** (Step 3)

**Then plan migration to PostgreSQL before:**
- More than 5 users
- Users in different shifts entering data simultaneously
- Production/permanent deployment

---

## 📞 Support

If you encounter issues during deployment, check:
- Django deployment docs: https://docs.djangoproject.com/en/5.0/howto/deployment/
- PostgreSQL setup: https://www.postgresql.org/docs/
- Security checklist: python manage.py check --deploy
