import io
import os
import google.auth
import environ
from datetime import timedelta
from google.cloud import secretmanager

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def location(x): return os.path.join(
    os.path.dirname(os.path.realpath(__file__)), x)


env = environ.Env(DEBUG=(bool, False), ALLOWED_HOSTS=(list, ['*']))
env.read_env()

PROJECT_NAME = os.environ.get('PROJECT_NAME')
VERSION = os.environ.get('VERSION', 'LOCAL')


BACKEND_URL = os.environ.get('BACKEND_URL', 'http://0.0.0.0')
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
FRONTEND_VERIFY_EMAIL_URL = FRONTEND_URL + '/verify-email'

CSRF_TRUSTED_ORIGINS = os.environ.get('CSRF_TRUSTED_ORIGINS').split(',')

IS_DEVELOPMENT = bool(int(os.environ.get('IS_DEVELOPMENT', False)))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(int(os.environ.get('DEBUG', False)))


try:
    _, os.environ['GOOGLE_CLOUD_PROJECT'] = google.auth.default()
    print('Success auth by google', os.environ['GOOGLE_CLOUD_PROJECT'])
except google.auth.exceptions.DefaultCredentialsError:
    pass

if not IS_DEVELOPMENT:
    # Pull secrets from Secret Manager
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')

    client = secretmanager.SecretManagerServiceClient()
    settings_name = os.environ.get('SETTINGS_NAME', 'django-settings')
    name = f'projects/{project_id}/secrets/{settings_name}/versions/latest'
    payload = client.access_secret_version(
        name=name).payload.data.decode('UTF-8')
    print(payload, 'settings loaded')
    env.read_env(io.StringIO(payload))
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    'SECRET_KEY', 'sdfm-bci^u39bw19op25fv@x)*zh7%!q!(@j3r1jez50--sdtd1w2132')


ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')
if DEBUG:
    ALLOWED_HOSTS += ['192.168.{}.{}'.format(i, j)
                      for i in range(256) for j in range(256)]
    ALLOWED_HOSTS += ['127.0.0.1', '0.0.0.0', 'localhost']

# Application definition

INSTALLED_APPS = [
    'user',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'hashids',
    'rest_framework',
    'drf_standardized_errors',  # Errors standardized
    'drf_spectacular',  # Swagger
    'drf_spectacular_sidecar',  # Swagger
    'nested_admin',
    'anymail',  # email sender

    'core',
    # 'twilio_sms', # Sms sender
    'mail',  # email by anymail
    'notifications',

]

ANYMAIL = {
    'SENDGRID_API_KEY': os.environ.get('SENDGRID_KEY'),
}

EMAIL_BACKEND = "anymail.backends.sendgrid.EmailBackend"


CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://redis:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
]

CORS_ORIGIN_WHITELIST = os.environ.get('CORS_ORIGIN_WHITELIST').split(',')

ROOT_URLCONF = 'urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            location('templates')
        ],
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

WSGI_APPLICATION = 'wsgi.application'
X_FRAME_OPTIONS = 'SAMEORIGIN'

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'core.pagination.DefaultPager',
    'PAGE_SIZE': 100,
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    # Errors standardized
    'EXCEPTION_HANDLER': 'drf_standardized_errors.handler.exception_handler',
    # Swagger schema
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# Errors standardized
DRF_STANDARDIZED_ERRORS = {'ENABLE_IN_DEBUG_FOR_UNHANDLED_EXCEPTIONS': True}


# ---------------- SWAGGER ---------------- #
SPECTACULAR_SETTINGS = {
    'TITLE': f'{PROJECT_NAME} API',
    'DESCRIPTION': f'API documentation for {PROJECT_NAME} app',
    # CONTACT: Optional: MAY contain 'name', 'url', 'email'
    'CONTACT': {
        'name': f'{PROJECT_NAME}',
        'url': f'{FRONTEND_URL}',
    },
    # LICENSE: Optional: MUST contain 'name', MAY contain URL
    'LICENSE': {},
    'SERVERS': [{'url': f'{BACKEND_URL}', 'description': f'{VERSION}'},],
    'VERSION': f'{VERSION}',
    'SERVE_INCLUDE_SCHEMA': False,
    'SWAGGER_UI_DIST': 'SIDECAR',
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    # OTHER SETTINGS
    'SWAGGER_UI_SETTINGS': {
        'displayOperationId': True,
        'persistAuthorization': True,
        'filter': True,
        'tryItOutEnabled': True,
        'withCredentials': True,
    },
}
# COMMAND FOR CREATE SCHEMA
# docker-compose exec app python manage.py spectacular --color --file schema.yml

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=365),
    'UPDATE_LAST_LOGIN': True,
}

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',  # this is default
    'guardian.backends.ObjectPermissionBackend',
)

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases
if os.environ.get('DATABASE_URL'):
    db = env.db()
    print(env.db(), 'DATA_BASE_ACCESS')
else:
    db = {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': os.environ.get('DB_HOST'),
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASS'),
    }

DATABASES = {'default': db}

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Prague'

USE_I18N = True

USE_L10N = True

USE_TZ = True

AUTH_USER_MODEL = 'user.User'
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

GOOGLE_AUTH_BASE_URL = 'https://www.googleapis.com/oauth2/v3/userinfo?alt=json'
FACEBOOK_AUTH_BASE_URL = 'https://graph.facebook.com/v12.0/me/?fields=email,id,name'
APPLE_AUTH_BASE_URl = '?scope=name%20email%20sub'

DEFAULT_FILE_STORAGE = os.environ.get('STORAGE')
STATICFILES_STORAGE = os.environ.get('STATIC_STORAGE')
GS_STATIC_BUCKET_NAME = os.environ.get('GS_STATIC_BUCKET_NAME')
GS_MEDIA_BUCKET_NAME = os.environ.get('GS_MEDIA_BUCKET_NAME')

MEDIA_URL = os.environ.get('STORAGE_PUBLIC_PATH').format(GS_MEDIA_BUCKET_NAME)
MEDIA_ROOT = os.environ.get('STORAGE_MEDIA_ROOT')

STATIC_URL = os.environ.get(
    'STORAGE_PUBLIC_PATH').format(GS_STATIC_BUCKET_NAME)
STATIC_ROOT = os.environ.get('STORAGE_STATIC_ROOT')

MAX_UPLOAD_SIZE = 5242880

# --------- CELERY TASKS SCHEDULE --------- #
CELERY_BEAT_SCHEDULE = {
    # 'beat-health-check-every-minute': {
    #     'task': 'celery_test_task',
    #     'schedule': timedelta(minutes=1)
    # }
}

# ------------- CELERY TASKS -------------- #
CELERY_TASK_ROUTES = {
    # Celery health check / example task
    # 'celery_test_task': {'queue': 'main-queue'},

    'send_verify_email': {'queue': 'main-queue'},
    'send_password_reset_request_email': {'queue': 'main-queue'},
    'send_fire_push': {'queue': 'main-queue'},
}


# ----------------- SENTRY ---------------- #
SENTRY_DSN = os.environ.get('SENTRY_DSN')
sentry_sdk.init(
    dsn=SENTRY_DSN,
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,
    send_default_pii=True,
)

# ----------------- REDIS ----------------- #
REDIS_PORT = os.environ.get('REDIS_PORT')
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD')
REDIS_SERVER = os.environ.get('REDIS_SERVER')
REDIS_APP_DB = os.environ.get('REDIS_APP_DB')
CELERY_BROKER_URL = f'redis://:{REDIS_PASSWORD}@{REDIS_SERVER}/{REDIS_APP_DB}'
RESET_TOKEN_LENGTH = 5
RESET_CODE_EXPIRE = 3600


# ---------------- TWILIO ----------------- #
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_SERVICE_UID = os.environ.get('TWILIO_SERVICE_UID')

# ---------------- EMAILS ----------------- #
SENDGRID_KEY = os.environ.get('SENDGRID_KEY')
DEFAULT_EMAIL_FROM = os.environ.get('DEFAULT_EMAIL_FROM')
