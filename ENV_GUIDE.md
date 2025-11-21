**.env Guide**

This file explains the environment variables used by this project, how to obtain or generate their values, and safe handling practices for development and production.

**Quick Start**
- **Copy template**: Copy the example file into a working `.env` file: `cp env.example .env` (or on Windows PowerShell: `Copy-Item env.example .env`).
- **Edit**: Open `.env` and paste the values described below.

**Required Variables**
- **`SECRET_KEY`**: Django secret key used for cryptographic signing (sessions, CSRF, etc.).
  - How to get: generate a random key locally.
  - Example command (PowerShell): `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
  - Paste the printed value into `SECRET_KEY`.

- **`DEBUG`**: `True` or `False`. Use `True` for local development only.

- **`DATABASE_URL`**: Full database connection URL. Two common options:
  - SQLite (development): leave blank or set to `sqlite:///db.sqlite3` (project may already use local `db.sqlite3`).
  - PostgreSQL (production / dev with Postgres): `postgresql://<user>:<password>@<host>:<port>/<dbname>`
  - Example: `postgresql://consult_user:secretpass@localhost:5432/consultation_db`
  - How to get: install Postgres locally or use a managed DB; create a database and user; then build the URL above.

- **`GOOGLE_CLIENT_ID`** and **`GOOGLE_CLIENT_SECRET`**: Used for Google OAuth2 (django-allauth) and Google API access.
  - How to obtain:
    1. Visit the Google Cloud Console: `https://console.cloud.google.com/`.
    2. Create/select a project.
    3. Go to **APIs & Services > Credentials** and create **OAuth 2.0 Client IDs**.
    4. Set Authorized redirect URIs (for local dev):
       - `http://localhost:8000/accounts/google/login/callback/`
       - `http://localhost:8000/api/auth/google/callback/`
    5. Copy the **Client ID** and **Client Secret** and paste them into `.env`.

- **`ENCRYPTION_KEY`**: A symmetric key used by the app to encrypt sensitive fields.
  - How to generate: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
  - Paste the printed value into `ENCRYPTION_KEY`.

- **`CELERY_BROKER_URL`** and **`CELERY_RESULT_BACKEND`**: URLs for Celery broker and result backend (commonly Redis).
  - Local example (Redis): `redis://localhost:6379/0`
  - Confirm Redis is running: run `redis-server` or install via your OS package manager.

**Optional / Recommended Variables**
- **Email (SMTP)**: If the app sends email (bookings, reminders), set these values:
  - `EMAIL_HOST` (e.g., `smtp.gmail.com`) : mail server host
  - `EMAIL_PORT` (e.g., `587`) : SMTP port
  - `EMAIL_HOST_USER` : email account username
  - `EMAIL_HOST_PASSWORD` : email account password or app-specific password
  - `EMAIL_USE_TLS` : `True` or `False`
  - How to obtain: create an SMTP account or use a service (SendGrid, Mailgun). For Gmail, use an app password and allow SMTP access.

- **Third-party API keys** (if used): e.g., `GOOGLE_API_KEY`, `STRIPE_SECRET_KEY` — get them from each provider dashboard and keep them secret.

**Local Development Tips**
- Use `DEBUG=True` and a local SQLite DB for quick development: set `DATABASE_URL=sqlite:///db.sqlite3`.
- Use the `ENCRYPTION_KEY` and `SECRET_KEY` generated locally; do not reuse production keys in development.
- Start Redis locally for Celery: install Redis and run `redis-server`.

**Production & Security**
- **Never commit** the `.env` file into version control. Ensure `.gitignore` includes `.env` and `env.*`.
- Use environment-specific secrets stores for production:
  - GitHub Actions: store values in `Settings > Secrets` and reference them in workflows.
  - Cloud providers: use Azure Key Vault, AWS Secrets Manager, or GCP Secret Manager.
  - Platform-specific env settings: set environment variables in your hosting platform (Heroku, Azure Web Apps, Docker secrets).
- Use `DEBUG=False` in production and configure allowed hosts in Django settings.

**Docker / docker-compose**
- Add `.env` path to `docker-compose.yml` with `env_file:` so container reads environment variables.
- Example snippet in `docker-compose.yml`:
  env_file:
    - .env

**CI/CD**
- Do not put secrets into code or repository. Use pipeline secret stores and inject them at runtime.

**Checklist for new team members**
- Copy `env.example` to `.env`.
- Generate `SECRET_KEY` and `ENCRYPTION_KEY` (commands above).
- Ensure `DATABASE_URL` points to a reachable DB (or use SQLite for local dev).
- Obtain Google OAuth `CLIENT_ID` and `CLIENT_SECRET` and set redirect URIs.
- Configure SMTP or use a development email backend (console or file) if you don't have SMTP credentials.

**Need help?**
- If you'd like, I can:
  - Create a sanitized `.env.example` with placeholders for any missing variables.
  - Add a short script to auto-generate `SECRET_KEY` and `ENCRYPTION_KEY` and append them to `.env`.
  - Create a `docs/` page or a short video walkthrough for onboarding.

--
This guide is intended to match the variables and examples in `README.md`. If your `env.example` contains additional keys, tell me the filename and I will add tailored instructions for those too.
