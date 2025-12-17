# PythonAnywhere Deployment Steps

## The Problem
The `/consultations/` endpoint was returning a 500 error due to:
1. Django logging trying to write to a file in a read-only path on PythonAnywhere
2. Missing `select_related()` optimization causing potential database issues
3. Template tags not handling invalid rating values

## The Fix
All issues have been committed and pushed to GitHub:
- ✅ Made file logging optional (disabled by default)
- ✅ Added `select_related()` to optimize database queries
- ✅ Added error handling to template tag functions

## Deployment Steps (Do This Now on PythonAnywhere)

### Step 1: SSH into PythonAnywhere
```bash
# Use PythonAnywhere's bash console or SSH
cd /home/ConsultEase/consultease.pythonanywhere.com
```

### Step 2: Pull Latest Code
```bash
git pull origin main
```

### Step 3: Activate Virtual Environment
```bash
source ../consultease-venv/bin/activate
```

### Step 4: Install/Update Dependencies
```bash
pip install -r requirements.txt
```

### Step 5: Run Migrations (if needed)
```bash
python manage.py migrate
```

### Step 6: Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### Step 7: Reload Web App
Go to PythonAnywhere Dashboard → Web → Click "Reload" button for your web app

### Step 8: Test
Visit: https://consultease.pythonanywhere.com/consultations/

Should work now! ✅

---

## What Changed

### settings.py
- Made file logging **optional** with `LOG_TO_FILE` env variable (defaults to `False`)
- Logging now uses console handler only, avoiding file system errors
- Can be enabled later if needed by setting `LOG_TO_FILE=True` in `.env`

### frontend_views.py
- Added `select_related('student', 'professor')` to consultations query
- Prevents N+1 database queries
- Improves performance and reliability

### rating_tags.py
- Added try-except error handling in `star_rating()` function
- Added error handling in `rating_class()` filter
- Added error handling in `rating_badge_class()` filter
- Safely handles None, invalid strings, and non-numeric values

---

## Quick Verification

After reloading, test these:

1. **Simple Test**: Visit https://consultease.pythonanywhere.com/
   - Should load home page without 500 error

2. **Consultations Test**: Visit https://consultease.pythonanywhere.com/consultations/
   - Should load your consultations list

3. **Check PythonAnywhere Error Log**: 
   - Go to Web tab → Error log
   - Should NOT show the "Unable to configure handler 'file'" error anymore

---

## If Still Getting Errors

1. Check error log for new error messages
2. Run in bash: `python manage.py check` (check for issues)
3. Verify `.env` file exists and has required variables
4. Ensure database migrations are up to date: `python manage.py migrate`

---

## Commands Summary (Copy & Paste)
```bash
cd /home/ConsultEase/consultease.pythonanywhere.com
git pull origin main
source ../consultease-venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
# Then reload web app from dashboard
```

---

Last updated: December 17, 2025
