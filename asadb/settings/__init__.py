# Django settings for asadb project.
import os
import sys

SITE_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
SITE_WEB_PATH = ''

DEBUG = False
TEMPLATE_DEBUG = DEBUG

# Is this the main, production deployment?
# If not, we won't try to propagate things to other systems.
# (For example, no changing asa-official membership.)
PRODUCTION_DEPLOYMENT = False

ADMINS = (
    ('ASA Database Team', 'asa-db@mit.edu',),
)
SERVER_EMAIL = 'asa-db-auto@mit.edu'
DEFAULT_FROM_EMAIL = 'asa-db@mit.edu'

MANAGERS = ADMINS

DATABASES = {}

KRB_KEYTAB = None
KRB_PRINCIPAL = None

ENABLE_SCRIPTS_AUTH = True

COOKIES_PREFIX = "asadb_"
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True

LOGFILE = "asa-db.log"

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

DATETIME_FORMAT_PYTHON = "%c"

from local import *

SESSION_COOKIE_NAME = COOKIES_PREFIX + "sessionid"
CSRF_COOKIE_NAME = COOKIES_PREFIX + "csrftoken"

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = SITE_ROOT + '/media/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = SITE_WEB_PATH + '/media/'

STATIC_URL = SITE_WEB_PATH + '/static/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = SITE_WEB_PATH + '/media/admin/'

LOGIN_REDIRECT_URL  = SITE_WEB_PATH + '/'
LOGIN_URL  = SITE_WEB_PATH + '/accounts/login'
LOGOUT_URL = SITE_WEB_PATH + '/accounts/logout'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.load_template_source',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.messages.context_processors.messages",
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.request",
)

MIDDLEWARE_CLASSES = [
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'reversion.middleware.RevisionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

AUTHENTICATION_BACKENDS = [
    'groups.models.PerGroupAuthz',
    'django.contrib.auth.backends.ModelBackend',
]

if ENABLE_SCRIPTS_AUTH:
    MIDDLEWARE_CLASSES.append('mit.ScriptsRemoteUserMiddleware')
    AUTHENTICATION_BACKENDS.insert(0, 'mit.ScriptsRemoteUserBackend')


ROOT_URLCONF = 'asadb.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(SITE_ROOT, 'template'),
)

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.sites',
    'form_utils',
    'django_filters',
    'reversion',
    'south',
    'groups',
    'forms',
    'space',
)

from local_after import *
