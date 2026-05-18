from pathlib import Path
from decouple import config
from django.core.management.utils import get_random_secret_key

BASE_DIR = Path(__file__).resolve().parent.parent


def _resolve_secret_key() -> str:
    """Return SECRET_KEY from env, or generate+persist one on first run.

    A missing SECRET_KEY must NOT crash the app — fresh clones with no .env
    should still boot. We materialize a dev key into BASE_DIR/.secret_key
    (gitignored) so subsequent runs are stable.
    """
    key = config('SECRET_KEY', default='')
    if key:
        return key
    cache = BASE_DIR / '.secret_key'
    if cache.is_file():
        try:
            return cache.read_text(encoding='utf-8').strip() or get_random_secret_key()
        except Exception:
            pass
    new_key = get_random_secret_key()
    try:
        cache.write_text(new_key, encoding='utf-8')
    except Exception:
        pass
    return new_key


SECRET_KEY = _resolve_secret_key()

# DEV-MODE FLAGS — defaults make a fresh clone fully autonomous.
# Production: ENABLE_AUTH=true, DEV_PUBLIC_MODE=false, AUTO_BOOTSTRAP=false.
ENABLE_AUTH: bool = config('ENABLE_AUTH', default=False, cast=bool)
DEV_PUBLIC_MODE: bool = config('DEV_PUBLIC_MODE', default=True, cast=bool)
REQUIRE_ADMIN_FOR_DELETE: bool = config('REQUIRE_ADMIN_FOR_DELETE', default=True, cast=bool)

AUTO_BOOTSTRAP: bool = config('AUTO_BOOTSTRAP', default=True, cast=bool)
ALLOW_EMPTY_DATABASE: bool = config('ALLOW_EMPTY_DATABASE', default=True, cast=bool)
MOCK_EXTERNAL_SERVICES: bool = config('MOCK_EXTERNAL_SERVICES', default=True, cast=bool)

DEBUG = config('DEBUG', default=True, cast=bool)

# When DEBUG is False, enable checks expected by `manage.py check --deploy`.
# Use HTTPS in production (or terminate TLS at a reverse proxy and set
# SECURE_PROXY_SSL_HEADER). For local smoke tests with DEBUG=False over HTTP,
# set SECURE_SSL_REDIRECT=False in the environment (deploy check may still warn
# about W008 unless TLS is terminated upstream).
if not DEBUG:
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = config(
        'SECURE_HSTS_INCLUDE_SUBDOMAINS',
        default=True,
        cast=bool,
    )
    SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=True, cast=bool)

_allowed_hosts_raw = config('ALLOWED_HOSTS', default='*')
ALLOWED_HOSTS = ['*'] if _allowed_hosts_raw.strip() in ('', '*') else [h.strip() for h in _allowed_hosts_raw.split(',') if h.strip()]

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'drf_yasg',
    'corsheaders',
]

LOCAL_APPS = [
    'auth_app',
    'users',
    'campaigns',
    'donations',
    'fund_owner',
    'funds',
    'applications',
    'myapp',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# При необходимости временно отключи отдельные строки (например CSRF) — не удаляй, только комментируй.
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Было отключено для тестов (раскомментируй верхний MIDDLEWARE и удали этот блок, если снова нужен пустой стек):
# MIDDLEWARE = []
# SILENCED_SYSTEM_CHECKS = ["admin.E408", "admin.E409", "admin.E410"]

ROOT_URLCONF = 'config.urls'

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

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / config('DATABASE_NAME', default='db.sqlite3'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'users.User'

# AUTH DISABLED FOR DEVELOPMENT MODE when ENABLE_AUTH=false / DEV_PUBLIC_MODE=true.
# Production values are used automatically when ENABLE_AUTH=true.
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        ['rest_framework_simplejwt.authentication.JWTAuthentication']
        if ENABLE_AUTH
        else []
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        ['rest_framework.permissions.IsAuthenticated']
        if ENABLE_AUTH
        else ['rest_framework.permissions.AllowAny']
    ),
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    **({'DEFAULT_THROTTLE_RATES': {
        'change_password': '5/min',
        'login': '10/min',
        'register': '5/min',
    }} if ENABLE_AUTH else {}),
}

from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGIN_REGEXES = [r'.*']
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'https://*',
    'http://*',
]

SWAGGER_SETTINGS = {
    'USE_SESSION_AUTH': False,
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'JWT as: Authorization: Bearer <access>',
        },
    },
    'SWAGGER_UI_SETTINGS': {
        'persistAuthorization': True,
    },
    'TAGS_SORTER': 'alpha',
}

REDOC_SETTINGS = {
    'LAZY_RENDERING': False,
}

# MOCK EXTERNAL SERVICES: use console email backend in dev to avoid SMTP errors
if MOCK_EXTERNAL_SERVICES:
    # DEVELOPMENT MODE BYPASS — emails print to console, never hit SMTP
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER or config('DEFAULT_FROM_EMAIL', default='noreply@localhost')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'myapp': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
