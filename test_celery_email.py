#!/usr/bin/env python
"""
Test script to verify Celery and Email SMTP configuration.
Run this from the prof_consult directory.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'prof_consult'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prof_consult.settings')
django.setup()

from django.conf import settings
from django.core.mail import send_mail
from prof_consult.celery import app
import redis


def print_header(text):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")


def test_redis_connection():
    """Test Redis connection."""
    print_header("Testing Redis Connection")
    try:
        r = redis.Redis.from_url(settings.CELERY_BROKER_URL)
        r.ping()
        print("✓ Redis connection: SUCCESS")
        info = r.info()
        print(f"  Redis version: {info.get('redis_version', 'unknown')}")
        print(f"  Connected clients: {info.get('connected_clients', 'unknown')}")
        return True
    except Exception as e:
        print(f"✗ Redis connection: FAILED")
        print(f"  Error: {str(e)}")
        return False


def test_celery_config():
    """Test Celery configuration."""
    print_header("Testing Celery Configuration")
    print(f"✓ Celery app name: {app.main}")
    print(f"✓ Broker URL: {app.conf.broker_url}")
    print(f"✓ Result backend: {app.conf.result_backend}")
    print(f"✓ Task serializer: {app.conf.task_serializer}")
    print(f"✓ Timezone: {app.conf.timezone}")
    print(f"✓ Beat scheduler: {settings.CELERY_BEAT_SCHEDULER}")
    
    # Check beat schedule
    print("\nConfigured periodic tasks:")
    for task_name, task_config in settings.CELERY_BEAT_SCHEDULE.items():
        print(f"  - {task_name}: runs every {task_config['schedule']} seconds")
    
    return True


def test_task_discovery():
    """Test if Celery tasks are discovered."""
    print_header("Testing Task Discovery")
    
    # Force reload tasks
    try:
        import apps.notifications.tasks
        import apps.integrations.tasks
        print("✓ Task modules imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import task modules: {e}")
        return False
    
    # List discovered tasks
    custom_tasks = sorted([t for t in app.tasks.keys() if t.startswith('apps.')])
    
    if custom_tasks:
        print(f"\n✓ Found {len(custom_tasks)} custom tasks:")
        for task in custom_tasks:
            print(f"  - {task}")
        return True
    else:
        print("✗ No custom tasks found!")
        return False


def test_email_config():
    """Test email configuration."""
    print_header("Testing Email Configuration")
    print(f"✓ Email backend: {settings.EMAIL_BACKEND}")
    print(f"✓ Email host: {settings.EMAIL_HOST}")
    print(f"✓ Email port: {settings.EMAIL_PORT}")
    print(f"✓ Use TLS: {settings.EMAIL_USE_TLS}")
    print(f"✓ Host user: {settings.EMAIL_HOST_USER}")
    print(f"✓ Default from: {settings.DEFAULT_FROM_EMAIL}")
    
    # Check if credentials are set
    if not settings.EMAIL_HOST_USER or settings.EMAIL_HOST_USER == "your_smtp_username@example.com":
        print("\n⚠ WARNING: Email host user is not configured!")
        print("  Please update EMAIL_HOST_USER in .env file")
        return False
    
    if not settings.EMAIL_HOST_PASSWORD or settings.EMAIL_HOST_PASSWORD == "your_app_password_or_api_key":
        print("\n⚠ WARNING: Email host password is not configured!")
        print("  Please update EMAIL_HOST_PASSWORD in .env file")
        return False
    
    return True


def test_email_sending(test_email=None):
    """Test actual email sending."""
    print_header("Testing Email Sending")
    
    if not test_email:
        print("⚠ No test email provided. Skipping email send test.")
        print("  To test email sending, run: python test_celery_email.py your@email.com")
        return None
    
    try:
        print(f"Attempting to send test email to: {test_email}")
        send_mail(
            subject='Test Email from Consultation Scheduler',
            message='This is a test email to verify SMTP configuration.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[test_email],
            fail_silently=False,
        )
        print("✓ Email sent successfully!")
        print("  Check your inbox (and spam folder)")
        return True
    except Exception as e:
        print(f"✗ Failed to send email: {str(e)}")
        print("\nCommon issues:")
        print("  1. Invalid credentials (check EMAIL_HOST_USER and EMAIL_HOST_PASSWORD)")
        print("  2. Gmail: Need to use App Password, not regular password")
        print("  3. Less secure apps: May need to enable in Gmail settings")
        print("  4. Two-factor authentication: Required for Gmail App Passwords")
        return False


def test_celery_worker_status():
    """Check if Celery workers are running."""
    print_header("Checking Celery Worker Status")
    
    try:
        inspector = app.control.inspect()
        active_workers = inspector.active()
        
        if active_workers:
            print(f"✓ Found {len(active_workers)} active worker(s):")
            for worker_name in active_workers.keys():
                print(f"  - {worker_name}")
            return True
        else:
            print("⚠ No active Celery workers found!")
            print("\nTo start a Celery worker, run:")
            print("  celery -A prof_consult worker --loglevel=info")
            return False
    except Exception as e:
        print(f"⚠ Could not check worker status: {str(e)}")
        print("\nTo start a Celery worker, run:")
        print("  celery -A prof_consult worker --loglevel=info")
        return False


def test_celery_beat_status():
    """Check if Celery beat is running."""
    print_header("Checking Celery Beat Status")
    
    try:
        r = redis.Redis.from_url(settings.CELERY_BROKER_URL)
        # Check for beat-related keys in Redis
        beat_keys = r.keys('celery-beat-*')
        
        if beat_keys:
            print(f"✓ Celery Beat appears to be running")
            print(f"  Found {len(beat_keys)} beat-related keys in Redis")
            return True
        else:
            print("⚠ Celery Beat does not appear to be running!")
            print("\nTo start Celery Beat, run:")
            print("  celery -A prof_consult beat --loglevel=info")
            return False
    except Exception as e:
        print(f"⚠ Could not check beat status: {str(e)}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("  CELERY AND EMAIL SMTP CONFIGURATION TEST")
    print("="*60)
    
    test_email = sys.argv[1] if len(sys.argv) > 1 else None
    
    results = {
        'Redis Connection': test_redis_connection(),
        'Celery Configuration': test_celery_config(),
        'Task Discovery': test_task_discovery(),
        'Email Configuration': test_email_config(),
        'Celery Worker Status': test_celery_worker_status(),
        'Celery Beat Status': test_celery_beat_status(),
    }
    
    # Only test email sending if email is provided
    if test_email:
        results['Email Sending'] = test_email_sending(test_email)
    
    # Summary
    print_header("SUMMARY")
    
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result is True else ("✗ FAIL" if result is False else "⚠ SKIP")
        print(f"{status:<10} {test_name}")
    
    print(f"\nResults: {passed} passed, {failed} failed, {skipped} skipped")
    
    if failed == 0:
        print("\n✓ All tests passed! Celery and Email SMTP are configured correctly.")
    else:
        print("\n⚠ Some tests failed. Please review the errors above.")
    
    # Recommendations
    if not results.get('Celery Worker Status'):
        print("\n" + "="*60)
        print("  IMPORTANT: Start Celery Worker")
        print("="*60)
        print("Open a new terminal and run:")
        print("  cd prof_consult")
        print("  celery -A prof_consult worker --loglevel=info --pool=solo")
        print("\nNote: Use --pool=solo on Windows")
    
    if not results.get('Celery Beat Status'):
        print("\n" + "="*60)
        print("  IMPORTANT: Start Celery Beat")
        print("="*60)
        print("Open another terminal and run:")
        print("  cd prof_consult")
        print("  celery -A prof_consult beat --loglevel=info")


if __name__ == '__main__':
    main()
