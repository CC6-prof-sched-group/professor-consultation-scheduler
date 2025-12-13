# Database Setup Guide: Render + Supabase PostgreSQL

This guide walks you through setting up your Django project for deployment using **Render** as the hosting platform and **Supabase** for PostgreSQL database.

## Prerequisites

- GitHub account (for Render integration)
- Supabase account
- Your Django project pushed to GitHub
- Local environment variables configured

---

## Part 1: Set Up Supabase PostgreSQL Database

### Step 1: Create a Supabase Project

1. Visit [supabase.com](https://supabase.com) and sign in/create an account
2. Click **"New Project"** in your dashboard
3. Fill in the details:
   - **Project Name**: `professor-consultation-scheduler` (or your preference)
   - **Database Password**: Create a strong password (save this!)
   - **Region**: Choose closest to your users
   - **Pricing Plan**: Select appropriate tier (Free tier available)
4. Click **"Create new project"** and wait for initialization (3-5 minutes)

### Step 2: Get Database Connection Details

1. Once created, go to **Project Settings** → **Database**
2. You'll see the connection string. Look for these details:
   - **Host**: `db.XXXX.supabase.co`
   - **Port**: `5432`
   - **Database name**: `postgres` (default)
   - **Username**: `postgres`
   - **Password**: The one you created

3. The **DATABASE_URL** format is:
   ```
   postgresql://postgres:<PASSWORD>@db.XXXX.supabase.co:5432/postgres
   ```
   Replace `<PASSWORD>` with your database password.

### Step 3: Create Required Extensions (Optional but Recommended)

1. In Supabase, go to **SQL Editor**
2. Click **"New Query"** and run:
   ```sql
   CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
   CREATE EXTENSION IF NOT EXISTS "pgcrypto";
   ```
3. Click **"Run"** to execute

---

## Part 2: Prepare Your Django Project

### Step 1: Update Requirements

Your `requirements.txt` already has the necessary dependencies:
- ✅ `psycopg2-binary>=2.9.9` (PostgreSQL adapter)
- ✅ `dj-database-url>=2.1.0` (URL parsing)

No changes needed here.

### Step 2: Create `.env.production` File

In your project root (`d:\User\Von\Documents\Codes\professor-consultation-scheduler\`), create `.env.production`:

```env
# Database Configuration
DATABASE_URL=postgresql://postgres:<PASSWORD>@db.XXXX.supabase.co:5432/postgres

# Django Settings
SECRET_KEY=<YOUR_SECRET_KEY>
DEBUG=False
ALLOWED_HOSTS=your-domain.onrender.com,www.your-domain.onrender.com

# Google OAuth (from your existing setup)
GOOGLE_CLIENT_ID=<YOUR_GOOGLE_CLIENT_ID>
GOOGLE_CLIENT_SECRET=<YOUR_GOOGLE_CLIENT_SECRET>

# Encryption Key
ENCRYPTION_KEY=<YOUR_ENCRYPTION_KEY>

# Email Configuration (for production)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True

# Celery (if needed for background tasks)
CELERY_BROKER_URL=<REDIS_URL_FROM_RENDER>
CELERY_RESULT_BACKEND=<REDIS_URL_FROM_RENDER>
```

**Important**: Replace all `<...>` placeholders with actual values.

### Step 3: Update Django Settings

Your `settings.py` already uses `dj_database_url` which is perfect. Verify this section around line 89:

```python
database_url = config('DATABASE_URL', default=f'sqlite:///{BASE_DIR / "db.sqlite3"}')
try:
    DATABASES = {
        'default': dj_database_url.config(
            default=database_url,
            conn_max_age=600,
        )
    }
except Exception:
    # Fallback to SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
```

✅ This is correctly configured. It will automatically use the `DATABASE_URL` from your environment.

---

## Part 3: Deploy to Render

### Step 1: Create a Render Account

1. Visit [render.com](https://render.com)
2. Sign up with GitHub
3. Authorize Render to access your GitHub repos

### Step 2: Create Web Service

1. In Render dashboard, click **"New"** → **"Web Service"**
2. Select your GitHub repo: `professor-consultation-scheduler`
3. Fill in the details:
   - **Name**: `professor-consultation-scheduler`
   - **Environment**: `Python 3`
   - **Build Command**: 
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**: 
     ```bash
     gunicorn prof_consult.wsgi:application
     ```
   - **Instance Type**: Select appropriate tier

### Step 3: Add Environment Variables

1. In the Web Service settings, scroll to **Environment**
2. Click **"Add Environment Variable"** and add each variable from your `.env.production`:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | `postgresql://postgres:PASSWORD@db.XXXX.supabase.co:5432/postgres` |
| `SECRET_KEY` | Your Django secret key |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `your-service-name.onrender.com` |
| `GOOGLE_CLIENT_ID` | Your Google OAuth ID |
| `GOOGLE_CLIENT_SECRET` | Your Google OAuth secret |
| `ENCRYPTION_KEY` | Your encryption key |
| `EMAIL_HOST_USER` | Your email |
| `EMAIL_HOST_PASSWORD` | Your app password |

### Step 4: Install Gunicorn

Update your `requirements.txt` to include:

```
gunicorn>=21.0.0
whitenoise>=6.6.0
```

Then add to your `settings.py` MIDDLEWARE (around line 55):

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add this line
    'corsheaders.middleware.CorsMiddleware',
    # ... rest of middleware
]
```

### Step 5: Collect Static Files

Add to your `settings.py` (around line 139):

```python
# Static files configuration for production
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### Step 6: Create Render Build Script

Create `build.sh` in your project root:

```bash
#!/bin/bash
set -o errexit

pip install -r requirements.txt

python prof_consult/manage.py collectstatic --no-input
python prof_consult/manage.py migrate
```

Update Render build command to: `bash build.sh`

---

## Part 4: Post-Deployment Steps

### Step 1: Run Migrations

After deployment, Render will automatically run your build script. But you can also manually run migrations:

1. In Render dashboard, go to your Web Service
2. Click the **"Shell"** tab
3. Run:
   ```bash
   python prof_consult/manage.py migrate
   ```

### Step 2: Create Superuser

```bash
python prof_consult/manage.py createsuperuser
```

### Step 3: Test Connection

Visit your deployed URL and verify:
- ✅ Website loads
- ✅ Database operations work
- ✅ Admin panel at `/admin/` accessible
- ✅ API endpoints respond correctly

---

## Part 5: Troubleshooting

### Issue: "ALLOWED_HOSTS" Error

**Solution**: Add your Render domain to the `.env` file:
```env
ALLOWED_HOSTS=your-service.onrender.com,www.your-service.onrender.com
```

### Issue: Database Connection Failed

**Solution**: 
1. Verify `DATABASE_URL` is correct in Render environment variables
2. Test connection locally:
   ```bash
   python -c "import psycopg2; psycopg2.connect('your-database-url')"
   ```
3. Check Supabase firewall: Supabase allows all IPs by default

### Issue: Static Files Not Loading

**Solution**:
1. Ensure `whitenoise` is installed: `pip install whitenoise`
2. Run collectstatic locally: `python manage.py collectstatic`
3. Push changes to GitHub and redeploy

### Issue: Migrations Not Running

**Solution**:
1. Check Render build logs for errors
2. Manually run from Shell:
   ```bash
   python prof_consult/manage.py migrate
   ```
3. Verify all migration files exist in GitHub

---

## Part 6: Optional - Set Up Redis (for Celery Tasks)

If you're using Celery for background tasks:

### On Render:

1. Create **Redis** service:
   - Click **"New"** → **"Redis"**
   - Follow the setup wizard
   - Copy the **Internal Redis URL**

2. Add to environment variables:
   ```env
   CELERY_BROKER_URL=<RENDER_REDIS_URL>
   CELERY_RESULT_BACKEND=<RENDER_REDIS_URL>
   ```

3. Create Celery Worker:
   - Click **"New"** → **"Background Worker"**
   - Use same GitHub repo
   - Start Command: `celery -A prof_consult worker -l info`
   - Add same environment variables

---

## Quick Reference: Required Environment Variables

```env
DATABASE_URL=postgresql://postgres:PASSWORD@db.XXXX.supabase.co:5432/postgres
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-service.onrender.com
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
ENCRYPTION_KEY=your-encryption-key
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True
CELERY_BROKER_URL=your-redis-url (optional)
CELERY_RESULT_BACKEND=your-redis-url (optional)
```

---

## Monitoring & Maintenance

### Monitor Logs
- Render: Dashboard → Logs tab
- Supabase: Home → Database Usage

### Database Backups
- Supabase automatically backs up daily (free tier: 7 days retention)
- View in Supabase: Settings → Backups

### Performance
- Check slow queries in Supabase
- Monitor database connections
- Scale instance if needed

---

## Summary

1. ✅ Create Supabase project and get `DATABASE_URL`
2. ✅ Create `.env.production` with all variables
3. ✅ Install `gunicorn` and `whitenoise`
4. ✅ Update `settings.py` with static files config
5. ✅ Deploy to Render via GitHub
6. ✅ Set environment variables in Render dashboard
7. ✅ Run migrations via Render Shell
8. ✅ Test deployment

You're ready to deploy! 🚀
