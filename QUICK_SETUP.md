# Quick Setup Guide - Celery & Email

## ✅ What's Working
- Redis connection
- Celery configuration
- Task discovery (7 tasks found)
- Email templates (all exist)

## ⚠️ What Needs Fixing

### 1. Email Credentials (CRITICAL)
Edit: `prof_consult/.env`

```env
EMAIL_HOST_USER=your_actual_email@gmail.com
EMAIL_HOST_PASSWORD=your_16_char_app_password
DEFAULT_FROM_EMAIL=your_actual_email@gmail.com
```

**Get Gmail App Password:**
1. Enable 2FA on Google account
2. Visit: https://myaccount.google.com/apppasswords
3. Create new app password
4. Copy 16-character password to .env

### 2. Start Celery Worker (REQUIRED)

**Terminal 1:**
```powershell
cd prof_consult
..\venv\Scripts\Activate.ps1
celery -A prof_consult worker --loglevel=info --pool=solo
```

**Note:** `--pool=solo` is REQUIRED on Windows

### 3. Start Celery Beat (REQUIRED for periodic tasks)

**Terminal 2:**
```powershell
cd prof_consult
..\venv\Scripts\Activate.ps1
python manage.py migrate django_celery_beat
celery -A prof_consult beat --loglevel=info
```

### 4. Test Everything

**Terminal 3:**
```powershell
cd professor-consultation-scheduler
python test_celery_email.py your_email@example.com
```

## 🐛 Bug Fixed
- ✅ Removed conflicting `prof_consult/celery.py` file
- ✅ Fixed task autodiscovery issue
- ✅ Django now starts without import errors

## 📝 Full Details
See: `CELERY_EMAIL_ANALYSIS_REPORT.md`
