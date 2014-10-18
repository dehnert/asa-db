import os

_site_root = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))

DATABASES = {
    'default' : {
        'ENGINE' : 'django.db.backends.sqlite3',
        'NAME' : os.path.join(_site_root, 'asa-db.sqlite'),
    },
}

# Mail sending
# See https://docs.djangoproject.com/en/dev/topics/email/#email-backends
send_mail = True
send_mail = False
if send_mail:
    EMAIL_HOST = 'outgoing.mit.edu'
else:
    # Display intermixed with the error messages
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    # Or send to a custom server
    #EMAIL_HOST = 'localhost'
    #EMAIL_PORT = 1025
    # Run python -m smtpd -n -c DebuggingServer localhost:1025

# Make this unique, and don't share it with anybody.
#SECRET_KEY = something
# Generate the "something" with:
# import random; ''.join([random.choice('abcdefghijklmnopqrstuvwxyz0123456789@#%&-_=+') for i in range(50)])

SESSION_COOKIE_SECURE = False

DEBUG = False
DEBUG = True
