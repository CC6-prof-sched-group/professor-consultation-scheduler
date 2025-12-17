# ConsultEase - Professor Consultation Scheduling System

A comprehensive Django-based web application that enables students to book consultations with professors, featuring role-based access, Google Calendar integration, and automated email notifications.

**Live Demo**: [https://consultease.pythonanywhere.com/](https://consultease.pythonanywhere.com/)

## Features

- **User Authentication**: Secure login/signup via Google OAuth2 (django-allauth).
- **Role-Based Access**: Specialized dashboards for Students, Professors, and Administrators.
- **Consultation Booking**: Intuitive booking flow for students to schedule appointments.
- **Google Calendar Sync**: Automatically creates, updates, and deletes events in users' Google Calendars.
- **Smart Notifications**: 
    - Instant email notifications for bookings, confirmations, cancellations, and reschedules.
    - Automated 24-hour reminder emails (via management command).
- **Real-time Availability**: Professors manage their weekly schedule and specific slots.
- **Rating & Feedback**: Students can rate and review completed consultations.
- **Admin Dashboard**: Centralized management interface with system usage statistics.
- **RESTful API**: Full API coverage using Django REST Framework.

## Technology Stack

- **Backend**: Django 5.x
- **API**: Django REST Framework
- **Database**: PostgreSQL (Production) / SQLite (Development)
- **Authentication**: django-allauth with Google OAuth2
- **Calendar Integration**: Google Calendar API
- **Task Scheduling**: Custom Management Commands (Cron) 
- **Frontend**: Django Templates + Bootstrap / Custom CSS

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd prof-consult
```

### 2. Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Application Setup

1.  **Environment Variables**: rename `env.example` to `.env` and configure:
    ```env
    SECRET_KEY=your-secret-key
    DEBUG=True
    GOOGLE_CLIENT_ID=your-google-client-id
    GOOGLE_CLIENT_SECRET=your-google-client-secret
    ENCRYPTION_KEY=run-python-script-to-generate-this
    ```

2.  **Generate Encryption Key**:
    ```bash
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    ```
    Paste the output into `ENCRYPTION_KEY` in your `.env`.

3.  **Database Migration**:
    ```bash
    python manage.py migrate
    ```

4.  **Create Admin User**:
    ```bash
    python manage.py createsuperuser
    ```

### 5. Google OAuth2 Setup
1.  Go to [Google Cloud Console](https://console.cloud.google.com/).
2.  Enable **Google+ API** and **Google Calendar API**.
3.  Create OAuth Credentials.
4.  Add Redirect URIs:
    - `http://localhost:8000/accounts/google/login/callback/`
    - `http://localhost:8000/api/auth/google/callback/`

## Running the Application

### Development Server
```bash
python manage.py runserver
```
Visit `http://localhost:8000`.

### Background Tasks (Reminders)
To send 24-hour appointment reminders, run this command manually or set up a cron job:
```bash
python manage.py send_reminders
```

---

## Deployment on PythonAnywhere

### 1. Project Setup
1.  Open a **Bash** console.
2.  Clone the repo:
    ```bash
    git clone https://github.com/CC6-prof-sched-group/professor-consultation-scheduler.git
    ```
3.  Create and activate virtual environment:
    ```bash
    mkvirtualenv --python=/usr/bin/python3.13 consultease-venv
    pip install -r requirements.txt
    ```

### 2. Static Files & Database
```bash
# Collect static files
python manage.py collectstatic

# Run migrations
python manage.py migrate
```

### 3. Setting Validated Reminders (Scheduled Tasks)
Go to the **Tasks** tab in PythonAnywhere and add a daily task to run the reminders:
```bash
original_working_directory=/home/yourusername/professor-consultation-scheduler/prof_consult
/home/yourusername/.virtualenvs/consultease-venv/bin/python manage.py send_reminders
```

### 4. Web App Configuration
-   **Source code**: `/home/yourusername/professor-consultation-scheduler/prof_consult`
-   **WSGI configuration file**: Update with your project settings path.
-   **Static files**:
    -   URL: `/static/`
    -   Path: `/home/yourusername/professor-consultation-scheduler/prof_consult/staticfiles`


## Authors

### Project Members

-   [Vougne Froid Alis](https://github.com/VougneFroid)
-   [Efren Johannes Bucao](https://github.com/Frendsb)
-   [Kenneth Castillo](https://github.com/CastleKen)
-   [Kenneth Batoctoy](https://github.com/Kenshta)
-   [Mark Jayson Galarpe](https://github.com/Markgalarpe)
-   [Ricalyn Olayvar](https://github.com/RicsOlayvar)


