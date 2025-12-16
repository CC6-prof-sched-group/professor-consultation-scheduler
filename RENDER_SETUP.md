# Render Deployment Setup Guide

## Critical Environment Variables for Render

Add these environment variables in your Render dashboard (Settings > Environment):

### Required for Basic Operation
```
SECRET_KEY=<generate-with-django>
DEBUG=False
ALLOWED_HOSTS=your-app-name.onrender.com
SITE_DOMAIN=your-app-name.onrender.com
DATABASE_URL=<provided-by-render-postgres-addon>
```

### Required for Google OAuth
```
GOOGLE_CLIENT_ID=<from-google-cloud-console>
GOOGLE_CLIENT_SECRET=<from-google-cloud-console>
```

### Optional but Recommended
```
ENCRYPTION_KEY=<generate-with-fernet>
CELERY_BROKER_URL=<redis-url-if-using-celery>
CELERY_RESULT_BACKEND=<redis-url-if-using-celery>
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=<your-email>
EMAIL_HOST_PASSWORD=<app-password>
EMAIL_USE_TLS=True
```

## Google Cloud Console Setup

### Step 1: Configure OAuth Consent Screen
1. Go to https://console.cloud.google.com/
2. Select your project
3. Navigate to **APIs & Services > OAuth consent screen**
4. Fill in required fields (app name, user support email, etc.)

### Step 2: Create OAuth 2.0 Credentials
1. Go to **APIs & Services > Credentials**
2. Click **Create Credentials** > **OAuth 2.0 Client ID**
3. Choose **Web application**
4. Add **Authorized redirect URIs**:
   ```
   https://your-app-name.onrender.com/accounts/google/login/callback/
   https://your-app-name.onrender.com/api/auth/google/callback/
   ```
   Replace `your-app-name.onrender.com` with your actual Render domain.

5. Save and copy the **Client ID** and **Client Secret**
6. Add them to Render environment variables

### Step 3: Enable Required APIs
1. Go to **APIs & Services > Library**
2. Search for and enable:
   - Google Calendar API (if using calendar integration)
   - Google+ API (for profile data)

## Deployment Checklist

- [ ] Add all environment variables in Render
- [ ] Configure Google OAuth redirect URIs with production domain
- [ ] Set `DEBUG=False` in Render
- [ ] Set `ALLOWED_HOSTS` to your Render domain
- [ ] Set `SITE_DOMAIN` to your Render domain
- [ ] Configure PostgreSQL database (Render addon or external)
- [ ] Verify `build.sh` runs successfully
- [ ] Test Google OAuth login after deployment
- [ ] Check static files are loading (no MIME type errors)

## Troubleshooting

### Google OAuth Error: redirect_uri_mismatch
**Cause**: The redirect URI in Google Console doesn't match your actual domain.

**Solution**: 
1. Check your Render domain (e.g., `consult-ease-lz8p.onrender.com`)
2. Update `SITE_DOMAIN` environment variable to match exactly
3. Add the exact redirect URI to Google Console:
   `https://your-actual-domain.onrender.com/accounts/google/login/callback/`
4. Redeploy the app

### Static Files Not Loading (MIME Type Errors)
**Cause**: Static files not collected or WhiteNoise misconfigured.

**Solution**:
1. Verify `build.sh` includes `collectstatic --no-input`
2. Check that WhiteNoise middleware is in settings
3. Ensure `STORAGES` configuration is correct
4. Redeploy and check build logs

### 500 Internal Server Error
**Cause**: Usually missing environment variables or database issues.

**Solution**:
1. Check Render logs for specific error
2. Verify all required environment variables are set
3. Ensure database migrations ran successfully
4. Check `update_site_domain` command ran in build script

## Build Script (build.sh)

Your `build.sh` should contain:
```bash
#!/bin/bash
set -o errexit

pip install -r requirements.txt

python prof_consult/manage.py collectstatic --no-input
python prof_consult/manage.py migrate
python prof_consult/manage.py update_site_domain
```

## Verifying Deployment

After deployment, test these endpoints:
1. **Health Check**: `https://your-app.onrender.com/health/`
2. **Admin Panel**: `https://your-app.onrender.com/admin/`
3. **Google OAuth**: Try logging in with Google
4. **Static Files**: Check that CSS/JS loads without MIME errors in browser console

## Local vs Production Differences

| Setting | Local | Production (Render) |
|---------|-------|---------------------|
| DEBUG | True | False |
| ALLOWED_HOSTS | localhost,127.0.0.1 | your-app.onrender.com |
| SITE_DOMAIN | localhost:8000 | your-app.onrender.com |
| DATABASE | SQLite | PostgreSQL |
| OAuth Redirect | http://localhost:8000/... | https://your-app.onrender.com/... |
