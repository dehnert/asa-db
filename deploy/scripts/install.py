#!/usr/bin/env python

import argparse
import os, os.path
import random
import subprocess

def parse_args():
    parser = argparse.ArgumentParser(description="install the ASA DB on scripts")
    parser.add_argument('--db', default=None, help='database name to use; by default, derived from ADDREND')
    parser.add_argument('--legacy-db-exists', action='store_true', help='indicate that a pre-Django-1.8 database already exists, and it should merely be added to config and initial migrations marked as complete')
    parser.add_argument('--locker', help='locker to install into')
    parser.add_argument('--source', default='https://github.com/dehnert/asa-db@venv',
        help='URL of the git repo to install the ASA DB from')
    parser.add_argument('addrend', help='subdirectory of Scripts/django and web_scripts to install into')

    args = parser.parse_args()
    if not args.locker:
        args.locker = os.environ['LOGNAME']

    print args
    return args

def gen_secret_key():
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789@#%&-_=+'
    return ''.join([random.choice(chars) for i in range(50)])

class InstallASADB(object):
    def __init__(self, args):
        self.args = args

    def _run_ssh_helper(self, func, cmd):
        ssh = '/mit/scripts/bin/scripts-ssh'
        cmd = [ssh, self.args.locker] + cmd
        print(cmd)
        return func(cmd)

    def run_ssh(self, cmd):
        return self._run_ssh_helper(subprocess.check_call, cmd)

    def run_ssh_output(self, cmd):
        return self._run_ssh_helper(subprocess.check_output, cmd)

    def create_dirs(self):
        perms = (
            ('system:anyuser', 'none'),
            ('system:authuser', 'none'),
            ('daemon.scripts', 'write'),
        )
        django_dir = os.path.join('/mit', self.args.locker, 'Scripts/django')
        self.install_dir = os.path.join(django_dir, self.args.addrend)
        self.web_dir = os.path.join('/mit', self.args.locker, 'web_scripts', self.args.addrend)
        os.makedirs(self.install_dir)
        os.makedirs(self.web_dir)
        for new_dir in (django_dir, self.install_dir, self.web_dir):
            for group, bits in perms:
                subprocess.check_call(['fs', 'setacl', new_dir, group, bits])

    def create_db(self):
        if self.args.legacy_db_exists:
            print("Skipping DB creation, as requested")
            self.db = self.args.db
            return
        getter = '/mit/scripts/sql/bin/get-next-database'
        self.db = self.run_ssh_output([getter, self.args.db or self.args.addrend])
        if self.args.db:
            db_user, plus, db_name = self.args.db.partition('+')
            if self.db != db_name:
                raise ValueError('Database "%s" already exists' % (self.args.db, ))
        print("Creating database %s" % (self.db, ))
        creator = '/mit/scripts/sql/bin/create-database'
        self.run_ssh([creator, self.db])

    def install_source(self):
        subprocess.check_call(['virtualenv', '--prompt=(venv/asa)', self.install_dir])
        pip = os.path.join(self.install_dir, 'bin/pip')
        src = 'git+%s#egg=asa-db' % (self.args.source, )
        subprocess.check_call([pip, 'install', '--editable', src])

    def install_web_scripts(self):
        install_base = "../Scripts/django/%s/src/asadb" % (self.args.addrend, )
        os.symlink(os.path.join(install_base, "asadb/media/"), os.path.join(self.web_dir, 'media'))
        os.symlink(os.path.join(install_base, "deploy/scripts/index.fcgi"), os.path.join(self.web_dir, 'index.fcgi'))

    def configure(self):
        pass

    def install(self):
        self.create_dirs()
        #self.create_db()
        self.install_source()
        self.configure()

if __name__ == '__main__':
    InstallASADB(parse_args()).install()
