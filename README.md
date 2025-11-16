# Professor Consultation Scheduling System

A comprehensive Django-based web application that enables students to book consultations with professors, with role-based access for students, professors, and administrators.

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

## Technology Stack

- **Backend**: Django 5.x
- **API**: Django REST Framework
- **Database**: PostgreSQL (SQLite for development)
- **Authentication**: django-allauth with Google OAuth2
- **Task Queue**: Celery with Redis
- **Calendar Integration**: Google Calendar API
- **Email**: Django email backend (configurable for SMTP)

## Prerequisites

- Python 3.11+
- PostgreSQL (or SQLite for development)
- Redis (for Celery)
- Google OAuth2 credentials
- Virtual environment (recommended)

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

## Project Structure

```
prof_consult/
├── apps/
│   ├── accounts/          # User model, authentication
│   │   ├── models.py      # Custom User model
│   │   ├── views.py       # Authentication views
│   │   ├── serializers.py # User serializers
│   │   ├── permissions.py # Custom permissions
│   │   └── admin.py       # Admin configuration
│   ├── consultations/     # Consultation models, views
│   │   ├── models.py      # Consultation model
│   │   ├── views.py       # Consultation ViewSet
│   │   ├── serializers.py # Consultation serializers
│   │   └── admin.py       # Admin configuration
│   ├── professors/        # Professor profiles
│   │   ├── models.py      # ProfessorProfile model
│   │   ├── views.py       # Professor ViewSet
│   │   ├── serializers.py # Professor serializers
│   │   └── admin.py       # Admin configuration
│   ├── notifications/     # Notification system
│   │   ├── models.py      # Notification model
│   │   ├── views.py       # Notification ViewSet
│   │   ├── tasks.py       # Celery tasks for emails
│   │   └── admin.py       # Admin configuration
│   └── integrations/      # External integrations
│       ├── services.py    # Google Calendar service
│       └── tasks.py       # Calendar sync tasks
├── templates/             # Django templates
│   └── emails/           # Email templates
├── static/               # Static files (CSS, JS)
├── config/               # Configuration files
├── prof_consult/         # Main project settings
│   ├── settings.py       # Django settings
│   ├── urls.py          # URL configuration
│   ├── celery.py        # Celery configuration
│   └── wsgi.py          # WSGI configuration
├── manage.py            # Django management script
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## API Endpoints

### Authentication

- `POST /api/auth/google/` - Initiate Google OAuth2 flow
- `GET /api/auth/google/callback/` - Handle OAuth2 callback
- `POST /api/auth/logout/` - Logout user
- `GET /api/auth/user/` - Get current user details
- `POST /api/auth/token/` - Get authentication token

### Professors

- `GET /api/professors/` - List all professors (with filters: department, availability)
- `GET /api/professors/{id}/` - Get professor details
- `GET /api/professors/{id}/availability/` - Get professor's available time slots
- `PUT /api/professors/{id}/availability/` - Update availability (professor only)

### Consultations

- `GET /api/consultations/` - List consultations (filtered by role and status)
- `POST /api/consultations/` - Create new consultation booking (students)
- `GET /api/consultations/{id}/` - Get consultation details
- `PATCH /api/consultations/{id}/confirm/` - Confirm consultation (professor)
- `PATCH /api/consultations/{id}/cancel/` - Cancel consultation
- `PATCH /api/consultations/{id}/reschedule/` - Reschedule consultation
- `PATCH /api/consultations/{id}/complete/` - Mark as completed (professor)
- `PATCH /api/consultations/{id}/no-show/` - Mark as no-show (professor)
- `POST /api/consultations/{id}/notes/` - Add notes (professor)
- `POST /api/consultations/{id}/rate/` - Rate consultation (student, after completion)

### Admin

- `GET /api/admin/users/` - List all users
- `GET /api/admin/consultations/` - All consultations with advanced filters
- `GET /api/admin/statistics/` - Dashboard statistics
- `PATCH /api/admin/users/{id}/role/` - Update user role

### Notifications

- `GET /api/notifications/` - Get user notifications
- `PATCH /api/notifications/{id}/read/` - Mark notification as read

## Usage Examples

### Creating a Consultation (Student)

```python
POST /api/consultations/
{
    "professor_id": 1,
    "title": "Help with Assignment 3",
    "description": "I need help understanding the concepts in Assignment 3",
    "scheduled_date": "2024-12-01",
    "scheduled_time": "14:00:00",
    "duration": 30,
    "location": "Room 101"
}
```

### Confirming a Consultation (Professor)

```python
PATCH /api/consultations/{id}/confirm/
```

### Rating a Consultation (Student)

```python
POST /api/consultations/{id}/rate/
{
    "rating": 5,
    "feedback": "Very helpful session!"
}
```

## Testing

Run tests using pytest:

```bash
pytest
```

Or using Django's test runner:

```bash
python manage.py test
```

## Security Considerations

- **Encrypted Tokens**: Google OAuth tokens are encrypted in the database
- **HTTPS**: Use HTTPS in production
- **CSRF Protection**: Enabled by default
- **Rate Limiting**: Configured on API endpoints
- **Input Validation**: All inputs are validated
- **SQL Injection Protection**: Django ORM provides protection

## Deployment Checklist

- [ ] Set `DEBUG=False` in production settings
- [ ] Configure environment variables
- [ ] Set up PostgreSQL database
- [ ] Configure static file serving (WhiteNoise or S3)
- [ ] Set up Redis for Celery
- [ ] Configure SSL certificate
- [ ] Set up email service (SendGrid, Mailgun, etc.)
- [ ] Configure Google OAuth2 for production domain
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy
- [ ] Set up error tracking (Sentry, etc.)

## Development

### Running Tests

```bash
pytest
```

### Code Style

Follow PEP 8 and Django coding standards. Use Black for code formatting:

```bash
black .
```

### Migrations

Create migrations after model changes:

```bash
python manage.py makemigrations
python manage.py migrate
```

## Troubleshooting

### Celery not running

Ensure Redis is running:

```bash
redis-cli ping
```

Should return `PONG`.

### Google Calendar integration not working

1. Verify Google OAuth2 credentials are correct
2. Check that Google Calendar API is enabled
3. Verify user has granted calendar permissions
4. Check logs for authentication errors

### Email not sending

1. Check email configuration in `.env`
2. For development, emails are printed to console by default
3. Check Celery worker logs for errors
4. Verify email backend configuration

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write tests
5. Submit a pull request

## License

[Add your license here]

## Support

For issues and questions, please open an issue on GitHub.

