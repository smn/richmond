# Django settings for webapp project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

from os.path import abspath, join, dirname, basename
APP_ROOT = abspath(join(dirname(__file__),'..'))
PROJECT_NAME = basename(APP_ROOT)

MANAGERS = ADMINS

DATABASE_ENGINE = 'postgresql_psycopg2'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = 'richmond'             # Or path to database file if using sqlite3.
DATABASE_USER = 'richmond'             # Not used with sqlite3.
DATABASE_PASSWORD = 'richmond'         # Not used with sqlite3.
DATABASE_HOST = 'localhost'            # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'UTC'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'x-4ce&vmrq4i%rkzhd0j^%$-%t%l1%@g_9m4eyqdc%#s=74(dh'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
    'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'richmond.webapp.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    join(APP_ROOT, 'webapp', 'templates'),
)

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'richmond.webapp.api',
    'celery',
)

# link our profile to the django.contrib.auth.models.User
AUTH_PROFILE_MODULE = 'api.Profile'

# we want our workers to be async
RICHMOND_WORKERS_ASYNC = False

# for Piston
PISTON_DISPLAY_ERRORS = True

# for Celery
BROKER_HOST = "localhost"
BROKER_PORT = 5672
BROKER_USER = "richmond"
BROKER_PASSWORD = "richmond"
BROKER_VHOST = "/richmond"

if DEBUG:
    CELERYD_LOG_LEVEL = 'DEBUG'
    CELERYD_LOG_FILE = None
else:
    CELERYD_LOG_FILE = 'logs/richmond.celeryd.log'

CELERY_QUEUES = {
    "default": {
        "exchange": "richmond",
        "binding_key": "richmond.webapp",
    },
    "sms_send": {
        "exchange": "richmond",
        "binding_key": "richmond.webapp.sms.send",
    },
    "sms_receive": {
        "exchange": "richmond",
        "binding_key": "richmond.webapp.sms.receive",
    },
    "sms_receipt": {
        "exchange": "richmond",
        "binding_key": "richmond.webapp.sms.receipt",
    },
}
CELERY_DEFAULT_QUEUE = "default"
CELERY_DEFAULT_EXCHANGE_TYPE = "direct"
CELERY_DEFAULT_ROUTING_KEY = "richmond.webapp"
# set the environment RICHMOND_SKIP_QUEUE to have the Celery tasks evaluated
# immediately, skipping the queue.
import os
CELERY_ALWAYS_EAGER = os.environ.get('RICHMOND_SKIP_QUEUE', False)

# for Clickatell
from clickatell import constants as cc
CLICKATELL_USERNAME = ''
CLICKATELL_PASSWORD = ''
CLICKATELL_API_ID = ''
CLICKATELL_DEFAULTS = {
    'sendmsg': {
        'callback': cc.CALLBACK_ALL,
        'deliv_ack': cc.YES,
        'req_feat': cc.FEAT_ALPHA + cc.FEAT_NUMER + cc.FEAT_DELIVACK,
        'msg_type': cc.SMS_DEFAULT,
    }
}

# for Opera
OPERA_SERVICE_ID = ''
OPERA_PASSWORD = ''
OPERA_CHANNEL = ''

# for E-Scape
E_SCAPE_API_ID = ''
E_SCAPE_SMSC = ''

# for Techsys
TECH_SYS_SMS_GATEWAY_URL = ''
TECH_SYS_SMS_GATEWAY_BIND = ''
