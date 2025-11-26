# Celery, Redis & SMTP Setup Guide

This guide will help you set up Celery (task queue), Redis (message broker), and Gmail SMTP (email sending) for the Professor Consultation Scheduler application.

---

## Prerequisites

- Python virtual environment activated
- Two Gmail accounts for testing (one for student, one for professor)
- Google Cloud Console project configured for OAuth

---

## Part 1: Redis Installation & Setup

### Step 1: Download Redis for Windows

Download Redis from this link:  
**[Redis for Windows](https://drive.google.com/file/d/13BVd1_W55XRnuUHpjbeF5vnY5y9wy5s7/view?usp=sharing)**

> **Alternative**: You can also download from [redis.io](https://redis.io/download) or use [Memurai](https://www.memurai.com/) (Redis-compatible for Windows)

### Step 2: Run Redis Server

1. Navigate to the folder where you extracted Redis
2. Double-click `redis-server.exe` to start the Redis server
3. Keep this window open - Redis must be running for Celery to work

### Step 3: Verify Redis is Running

Open a terminal and run:
```bash
redis-cli ping
```

**Expected output:**
```
PONG
```

If you see `PONG`, Redis is running successfully! 

---

## Part 2: Gmail SMTP Configuration

### Step 1: Enable 2-Step Verification

1. Go to your Google Account: [myaccount.google.com](https://myaccount.google.com)
2. Navigate to **Security** → **2-Step Verification**
3. Follow the prompts to enable it

### Step 2: Generate App Password

1. Visit [Google App Passwords](https://myaccount.google.com/apppasswords)
2. Select **Mail** as the app
3. Select your device or choose **Other** and enter "Django App"
4. Click **Generate**
5. Google will show you a 16-character password (e.g., `abcd efgh ijkl mnop`)
6. **Important**: Copy this password and **remove all spaces** → `abcdefghijklmnop`

### Step 3: Configure Environment Variables

Navigate to your project's `prof_consult` directory and open the `.env` file.

Update the following variables:

```env
# Email Settings (Gmail SMTP)
EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST="smtp.gmail.com"
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER="your-email@gmail.com"              # Replace with your Gmail address
EMAIL_HOST_PASSWORD="abcdefghijklmnop"              # Replace with your App Password (NO SPACES!)
DEFAULT_FROM_EMAIL="your-email@gmail.com"           # Replace with your Gmail address
SERVER_EMAIL="your-email@gmail.com"                 # Replace with your Gmail address
```

Remove ALL spaces from the `EMAIL_HOST_PASSWORD`. Google displays it with spaces, but Django needs it as one continuous string.

---

## Part 3: Running Celery Worker

### Step 1: Activate Virtual Environment

```bash
# Navigate to your project root
cd professor-consultation-scheduler

# Activate virtual environment
.\venv\Scripts\Activate.ps1
```

### Step 2: Navigate to Django Project Directory

```bash
cd prof_consult
```

### Step 3: Start Celery Worker

```bash
celery -A prof_consult worker --loglevel=info --pool=solo
```

**Keep this terminal open** - Celery must be running to process email tasks.

### Step 4: Start Django Development Server (Separate Terminal)

Open a **new terminal** and run:

```bash
# Activate venv
.\venv\Scripts\Activate.ps1

# Navigate to project
cd prof_consult

# Run server
python manage.py runserver
```

---

## Part 4: Testing Email Notifications

### Step 1: Register Two Google Accounts

1. Prepare two Gmail accounts:
   - **Account A**: Will be the Professor
   - **Account B**: Will be the Student

2. Register both accounts in [Google Cloud Console](https://console.cloud.google.com):
   - Go to your OAuth consent screen
   - Add both email addresses as **Test Users**
   - This allows them to sign in via Google OAuth

> **Note**: You can also sign up directly on the application without Google OAuth

### Step 2: Create Professor Account

1. **Sign in** with Account A
2. Go to **Profile** → **Account Settings**
3. Scroll to the bottom and click **"Convert to Professor"**
4. Fill in professor details and submit
5. **Sign out** from Account A

### Step 3: Book a Consultation (As Student)

1. **Sign in** with Account B (Student account)
2. Click on **"Professors"** tab in the navigation
3. Find the professor (Account A) in the list
4. Click **"Book Consultation"**
5. Fill in consultation details:
   - Title
   - Description
   - Date and Time
   - Duration
6. Click **"Confirm"** to submit the booking

### Step 4: Confirm Consultation (As Professor)

1. **Sign out** from Account B
2. **Sign in** with Account A (Professor account)
3. Go to **"Dashboard"**
4. You should see the pending consultation request
5. Click **"Confirm"** button

### Step 5: Check Email

📧 **The student (Account B) should receive an email notification** with:
- Confirmation message
- Consultation title
- Professor name
- Date and time
- Duration
- Location (if provided)
- Meeting link (if provided)

---

## Troubleshooting

### Issue: Email Not Received

**Solution**: Restart the Celery worker

```bash
# In the Celery terminal, press Ctrl+C to stop
# Then restart:
celery -A prof_consult worker --loglevel=info --pool=solo
```

The Celery worker caches environment variables, so it needs to be restarted after `.env` changes.

### Issue: Redis Connection Error

**Check if Redis is running:**
```bash
redis-cli ping
```

If no response, start `redis-server.exe` again.

### Issue: SMTP Authentication Error

**Verify your App Password:**
- Make sure you removed ALL spaces
- Make sure you're using an App Password, not your regular Gmail password
- Check that 2-Step Verification is enabled

**Test SMTP directly:**
```bash
python manage.py shell
```

```python
from django.core.mail import send_mail
send_mail('Test', 'Testing SMTP', 'your-email@gmail.com', ['recipient@gmail.com'])
```

### Issue: Celery Tasks Not Processing

**Check Celery logs** in the terminal where it's running for error messages.

**Verify Redis connection:**
```python
# In Django shell
from django.conf import settings
print(settings.CELERY_BROKER_URL)
```


---

## Running in Production

For production environments:

1. **Use a proper Redis server** (not redis-server.exe)
2. **Use environment-specific secrets** (Azure Key Vault, AWS Secrets Manager, etc.)
3. **Run Celery as a service** with supervisor or systemd
4. **Consider using Celery Beat** for scheduled tasks (reminders)
5. **Monitor Celery tasks** with Flower or similar tools

---

## Additional Notes

- **Keep Redis running** while the application is active
- **Keep Celery worker running** to process background tasks
- **Never commit** `.env` file to version control
- **Use different App Passwords** for development and production
- **Check spam folder** if emails don't appear in inbox

---

## Quick Reference Commands

```bash
# Check Redis
redis-cli ping

# Activate venv
.\venv\Scripts\Activate.ps1

# Start Celery Worker
celery -A prof_consult worker --loglevel=info --pool=solo

# Start Django Server
python manage.py runserver

# Test email in Django shell
python manage.py shell
from django.core.mail import send_mail
send_mail('Test', 'Message', 'from@gmail.com', ['to@gmail.com'])
```

---

Your application is now configured to send email notifications when professors confirm consultations.
