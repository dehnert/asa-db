import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'user+db',    # XXX: fix the database
        'OPTIONS': {
            'read_default_file' : os.path.expanduser('~/.my.cnf'),
        },
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# Mail sending
# See https://docs.djangoproject.com/en/dev/topics/email/#email-backends
send_mail = True
send_mail = False
if send_mail:
    EMAIL_HOST = 'outgoing.mit.edu'
else:
    EMAIL_BACKEND = 'util.emailbackend.ForcedRecipientEmailBackend'
    EMAIL_FORCED_RECIPIENTS = ['testing@mit.edu', ] # XXX: change the recipient
    EMAIL_FORCED_RECIPIENTS_LABEL = 'asa-db-forced-recipient@mit.edu'

# XXX: Make this unique, and don't share it with anybody.
#SECRET_KEY = something
# Generate the "something" with:
# import random; ''.join([random.choice('abcdefghijklmnopqrstuvwxyz0123456789@#%&-_=+') for i in range(50)])

SITE_SERVER = 'https://asa.scripts.mit.edu:444' # XXX: FIXME
SITE_WEB_PATH = '/asadb'    # XXX: FIXME
SITE_URL_BASE = SITE_SERVER

COOKIES_PREFIX = "asadb_"   # XXX: FIXME
