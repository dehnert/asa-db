import os
%(this_is_a_template_do_not_use_directly_see_deploy_scripts_install_py)s

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': '%(locker)s+%(db)s',
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
    EMAIL_FORCED_RECIPIENTS = ['asa-db-forced-recipient@mit.edu', ] # XXX: change the recipient
    EMAIL_FORCED_RECIPIENTS_LABEL = 'asa-db-forced-recipient@mit.edu'

# Make this unique, and don't share it with anybody.
SECRET_KEY = "%(secret_key)s"

SITE_SERVER = 'https://%(locker)s.scripts.mit.edu:444'
SITE_WEB_PATH = '/%(addrend)s'
SITE_URL_BASE = SITE_SERVER

COOKIES_PREFIX = "%(addrend)s_"
