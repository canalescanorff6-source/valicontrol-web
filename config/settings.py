from pathlib import Path
import os

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv('SECRET_KEY', 'dev-inseguro-troque-no-runsitex')
DEBUG = os.getenv('DEBUG', 'False').lower() in {'1', 'true', 'yes', 'on'}

ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver,.runsite.app').split(',') if h.strip()]
CSRF_TRUSTED_ORIGINS = [h.strip() for h in os.getenv('CSRF_TRUSTED_ORIGINS', 'https://*.runsite.app').split(',') if h.strip()]

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

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
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.app_info',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASE_URL = os.getenv('DATABASE_URL', '').strip()
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            ssl_require=DATABASE_URL.startswith(('postgres://', 'postgresql://')),
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Belem'
USE_I18N = True
USE_TZ = False

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SESSION_COOKIE_NAME = 'valicontrol_sessionid'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() in {'1', 'true', 'yes', 'on'}
CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', 'False').lower() in {'1', 'true', 'yes', 'on'}
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False').lower() in {'1', 'true', 'yes', 'on'}
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

ASAAS_API_KEY = os.getenv('ASAAS_API_KEY', '').strip()
ASAAS_BASE_URL = os.getenv('ASAAS_BASE_URL', 'https://api.asaas.com/v3').strip().rstrip('/')
APP_NAME = os.getenv('APP_NAME', 'ValiControl Web')
TRIAL_DIAS = int(os.getenv('TRIAL_DIAS', '15'))
TRIAL_LIMITE_PRODUTOS = int(os.getenv('TRIAL_LIMITE_PRODUTOS', '50'))
TRIAL_MAX_CONTAS_POR_IP = int(os.getenv('TRIAL_MAX_CONTAS_POR_IP', '2'))
PRO_LIMITE_PRODUTOS = int(os.getenv('PRO_LIMITE_PRODUTOS', '999999'))
VENCIMENTO_PROXIMO_DIAS = int(os.getenv('VENCIMENTO_PROXIMO_DIAS', '30'))
PIX_VALOR = float(os.getenv('PIX_VALOR', '10.00'))
PAGAMENTO_DESCRICAO = os.getenv('PAGAMENTO_DESCRICAO', 'Plano ValiControl PRO')
ASAAS_WEBHOOK_TOKEN = os.getenv('ASAAS_WEBHOOK_TOKEN', '').strip()
DATA_EXCEL_PATH = BASE_DIR / 'data' / 'dados.xlsx'
DATA_SQLITE_PATH = Path(os.getenv('DATA_SQLITE_PATH', BASE_DIR / 'data' / 'dados.sqlite3'))

# Cadastro autorizado por código enviado ao administrador
CADASTRO_AUTORIZACAO_OBRIGATORIA = os.getenv('CADASTRO_AUTORIZACAO_OBRIGATORIA', 'True').lower() in {'1', 'true', 'yes', 'on'}
CADASTRO_AUTORIZACAO_EMAIL = os.getenv('CADASTRO_AUTORIZACAO_EMAIL', os.getenv('CRIADOR_ADMIN_EMAILS', 'thiago01268230@gmail.com')).strip()
CADASTRO_AUTORIZACAO_WHATSAPP = os.getenv('CADASTRO_AUTORIZACAO_WHATSAPP', '5598996127032').strip()
CADASTRO_CODIGO_EXPIRA_MINUTOS = int(os.getenv('CADASTRO_CODIGO_EXPIRA_MINUTOS', '30'))
BREVO_API_KEY = os.getenv('BREVO_API_KEY', '').strip().strip('"').strip("'")
BREVO_SENDER_EMAIL = os.getenv('BREVO_SENDER_EMAIL', 'canalescanorff6@gmail.com').strip()
BREVO_SENDER_NAME = os.getenv('BREVO_SENDER_NAME', 'ValiControl Web').strip()
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', f'{BREVO_SENDER_NAME} <{BREVO_SENDER_EMAIL}>' if BREVO_SENDER_EMAIL else 'ValiControl Web <no-reply@localhost>')
EMAIL_TIMEOUT = int(os.getenv('EMAIL_TIMEOUT', '20'))

EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'core.email_backends.BrevoEmailBackend' if BREVO_API_KEY and BREVO_SENDER_EMAIL else 'django.core.mail.backends.console.EmailBackend')
