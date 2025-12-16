# Professor Consultation Scheduling System

A comprehensive Django-based web application that enables students to book consultations with professors, with role-based access for students, professors, and administrators.

**Live Demo**: https://consult-ease-lz8p.onrender.com

## Features

- **User Authentication**: Google OAuth2 authentication using django-allauth
- **Role-Based Access**: Separate roles for Students, Professors, and Administrators
- **Consultation Booking**: Students can book consultations with professors
- **Google Calendar Integration**: Automatic calendar event creation/update/deletion
- **Email Notifications**: Automated email notifications via Celery (booking created, confirmed, reminders, cancellations, reschedules)
- **Real-time Availability**: Professors can set and manage their availability
- **Rating System**: Students can rate completed consultations
- **Admin Dashboard**: Comprehensive admin interface with statistics
- **RESTful API**: Full REST API using Django REST Framework
- **Production Ready**: Configured for deployment on Render.com with PostgreSQL

## Technology Stack

- **Backend**: Django 5.x
- **API**: Django REST Framework
- **Database**: PostgreSQL (SQLite for development)
- **Authentication**: django-allauth with Google OAuth2
- **Task Queue**: Celery with Redis
- **Calendar Integration**: Google Calendar API
- **Email**: Django email backend (configurable for SMTP)


## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd prof-consult/prof_consult
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Copy `env.example` to `.env` and fill in the required values:

```bash
cp env.example .env
```

Edit `.env` with your configuration:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_URL=postgresql://user:password@localhost:5432/consultation_db
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
ENCRYPTION_KEY=your-encryption-key
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 5. Generate Encryption Key

Generate an encryption key for sensitive data:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Add this to your `.env` file as `ENCRYPTION_KEY`.

### 6. Set Up Database

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 7. Set Up Google OAuth2

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable Google+ API and Google Calendar API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URIs:
   - `http://localhost:8000/accounts/google/login/callback/`
   - `http://localhost:8000/api/auth/google/callback/`
6. Copy Client ID and Client Secret to `.env`

### 8. Run Migrations

```bash
python manage.py migrate
```

### 9. Create Superuser

```bash
python manage.py createsuperuser
```

## Running the Application

### Development Server

```bash
python manage.py runserver
```

The application will be available at `http://localhost:8000`

### Celery Worker (for background tasks)

In a separate terminal:

```bash
celery -A prof_consult worker -l info
```

### Celery Beat (for scheduled tasks)

In a separate terminal:

```bash
celery -A prof_consult beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### Redis (if not running)

```bash
redis-server
```
