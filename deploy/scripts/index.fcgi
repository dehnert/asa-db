#!/usr/bin/env python

# Shenanigans to run in the virtualenv when symlinked (*not* copied) into
# web_scripts
import os.path
real_this = os.path.realpath(__file__)
virtualenv_base = os.path.normpath(os.path.join(os.path.dirname(real_this), '../../../..'))
activate_this = os.path.join(virtualenv_base, 'bin/activate_this.py')
execfile(activate_this, dict(__file__=activate_this))

# Start of main code
import sys, os, time, threading, django.utils.autoreload
#sys.path.insert(0, os.path.join(virtualenv_base, "src/asadb/asadb"))
os.chdir(os.path.join(virtualenv_base, "src/asadb"))
os.environ['DJANGO_SETTINGS_MODULE'] = "asadb.settings"

def reloader_thread():
  while True:
    if django.utils.autoreload.code_changed():
      os._exit(3)
    time.sleep(1)
t = threading.Thread(target=reloader_thread)
t.daemon = True
t.start()

from django.core.servers.fastcgi import runfastcgi
runfastcgi(method="threaded", daemonize="false")
