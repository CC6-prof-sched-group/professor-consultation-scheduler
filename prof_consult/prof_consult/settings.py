"""
Django settings for prof_consult project.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.2/ref/settings/
"""
import os
import socket
from pathlib import Path

try:
    from decouple import config, Csv
    import dj_database_url
except ImportError:
    # Fallback if python-decouple is not installed
    def config(key, default=None, cast=None):
        value = os.environ.get(key, default)
        if cast and value is not None:
            return cast(value)
        return value
    
    def Csv(cast=str):
        """Fallback CSV parser that returns a callable"""
        def cast_csv(x):
            if not x:
                return []
            return [cast(item.strip()) for item in x.split(',') if item.strip()]
        return cast_csv
    
    def dj_database_url_config(default, **kwargs):
        return {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': Path(__file__).resolve().parent.parent / 'db.sqlite3'}}
    dj_database_url = lambda default, **kwargs: dj_database_url_config(default, **kwargs)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Logging paths and toggles
LOG_TO_FILE = config('LOG_TO_FILE', default=False, cast=bool)
LOG_DIR = BASE_DIR / 'logs'
LOG_FILE = LOG_DIR / 'django.log'

# Create log directory only if file logging is enabled
if LOG_TO_FILE:
    LOG_DIR.mkdir(exist_ok=True)

# Security Settings
SECRET_KEY = config('SECRET_KEY', default='django-insecure-z&je=#v1=nx&4kqqz==79+*+l9*(jtl=8es1a9g+7q3(wx!37*')
DEBUG = config('DEBUG', default=True, cast=bool)

# Allowed Hosts
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

# Site Domain (for django.contrib.sites and OAuth redirects)
SITE_DOMAIN = config('SITE_DOMAIN', default='localhost:8000')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    
    # Third-party apps
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.github',
    
    # Local apps
    'apps.accounts',
    'apps.consultations',
    'apps.professors',
    'apps.notifications',
    'apps.integrations',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'prof_consult.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'prof_consult.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
database_url = config('DATABASE_URL', default=f'sqlite:///{BASE_DIR / "db.sqlite3"}')
try:
    DATABASES = {
        'default': dj_database_url.config(
            default=database_url,
            conn_max_age=600,
        )
    }
except Exception:
    # Fallback to SQLite if dj_database_url fails
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Storage configuration (Django 4.2+)
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django Allauth Settings
# Dynamically select SITE_ID based on environment/hostname, override with env if set
_SITE_ID_VAL = config('SITE_ID', default=None)
try:
    SITE_ID = int(_SITE_ID_VAL) if _SITE_ID_VAL not in (None, '') else None
except (TypeError, ValueError):
    SITE_ID = None
if SITE_ID is None:
    # Check for PythonAnywhere environment
    is_pythonanywhere = (
        'pythonanywhere' in socket.gethostname() or 
        os.environ.get('PYTHONANYWHERE_DOMAIN') is not None
    )
    SITE_ID = 2 if is_pythonanywhere else 1

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Allauth Configuration (django-allauth 65+)
# Login/Logout URLs
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'
ACCOUNT_LOGOUT_ON_GET = True

# Login methods & signup fields
ACCOUNT_LOGIN_METHODS = {'username', 'email'}
ACCOUNT_SIGNUP_FIELDS = ['username*', 'email*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_UNIQUE_EMAIL = True
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'

# Google OAuth2 Settings
# Using SocialApplication model (configure via Django Admin at /admin/socialaccount/socialapp/)
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
            'https://www.googleapis.com/auth/calendar',
        ],
        'AUTH_PARAMS': {
            'access_type': 'offline',
            'prompt': 'consent',
        },
    }
}

# Optionally configure provider app credentials via settings (avoids manual DB SocialApp).
# If both env vars are present, allauth will use these instead of looking up SocialApp.
GOOGLE_CLIENT_ID_SETTING = config('GOOGLE_CLIENT_ID', default=None) or config('GOOGLE_OAUTH_CLIENT_ID', default=None)
GOOGLE_CLIENT_SECRET_SETTING = config('GOOGLE_CLIENT_SECRET', default=None) or config('GOOGLE_OAUTH_CLIENT_SECRET', default=None)
if GOOGLE_CLIENT_ID_SETTING and GOOGLE_CLIENT_SECRET_SETTING:
    SOCIALACCOUNT_PROVIDERS['google']['APP'] = {
        'client_id': GOOGLE_CLIENT_ID_SETTING,
        'secret': GOOGLE_CLIENT_SECRET_SETTING,
        'key': ''
    }

# Encryption Key for sensitive data
ENCRYPTION_KEY = config('ENCRYPTION_KEY', default=None)
if not ENCRYPTION_KEY:
    # Generate a key for development (DO NOT use in production)
    from cryptography.fernet import Fernet
    ENCRYPTION_KEY = Fernet.generate_key().decode()

# Google Calendar API Settings
GOOGLE_CALENDAR_API_KEY = config('GOOGLE_CALENDAR_API_KEY', default='')
GOOGLE_CALENDAR_ID = config('GOOGLE_CALENDAR_ID', default='primary')

# Django REST Framework Settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
    'DATE_FORMAT': '%Y-%m-%d',
    'TIME_FORMAT': '%H:%M:%S',
}

# CORS Settings
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000'
]
CORS_ALLOW_CREDENTIALS = True

# Email Settings
EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.console.EmailBackend'
)
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@consultation.com')

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        # Optional file handler to avoid startup errors on read-only paths
        **({
            'file': {
                'class': 'logging.FileHandler',
                'filename': str(LOG_FILE),
                'formatter': 'verbose',
            }
        } if LOG_TO_FILE else {})
    },
    'root': {
        'handlers': ['console'] + (['file'] if LOG_TO_FILE else []),
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'] + (['file'] if LOG_TO_FILE else []),
            'level': config('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'] + (['file'] if LOG_TO_FILE else []),
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Security Settings (for production)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Rate Limiting (using DRF)
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = [
    'rest_framework.throttling.AnonRateThrottle',
    'rest_framework.throttling.UserRateThrottle',
]
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '100/hour',
    'user': '1000/hour',
}
