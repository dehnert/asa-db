#!/usr/bin/python

import afs.pts
import ldap
import ldap.dn
import ldap.filter
import os
import sys
import subprocess

if __name__ == '__main__':
    cur_file = os.path.abspath(__file__)
    django_dir = os.path.abspath(os.path.join(os.path.dirname(cur_file), '..'))
    sys.path.append(django_dir)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import django.contrib.auth.models

import mit
import settings

class DjangoConnector(object):
    def __init__(self, ):
        self.dj_groups = django.contrib.auth.models.Group.objects

    def sync_helper(self, sys_name, dj_members, adder, remover, ):
        kept = []
        added = []
        nonexist = []
        created = []
        removed = []
        sys_members = self.get_members(sys_name)
        dj_usernames = set([m.username for m in dj_members])
        for username in sys_members:
            if username in dj_usernames:
                kept.append(username)
            else:
                # Need to add to the Django group
                try:
                    user, is_new = mit.get_or_create_mit_user(username, )
                    if is_new: created.append(username)
                    adder(user)
                    added.append(username)
                except ValueError:
                    nonexist.append(username)
        for user in dj_members:
            username = user.username
            if username in sys_members:
                assert username in kept
            else:
                remover(user)
                removed.append(username)
        return {
            'change' : len(added) + len(removed),
            'keep' : kept,
            'add'  : added,
            'create' : created,
            'nonexist' : nonexist,
            'remove': removed,
        }

    def sync_staff(self, sys_name, ):
        dj_members = django.contrib.auth.models.User.objects.filter(is_staff=True, )
        def adder(user, ):
            user.is_staff = True
            user.save()
        def remover(user, ):
            user.is_staff = False
            user.save()
        return self.sync_helper(sys_name, dj_members, adder, remover, )

    def sync_members(self, sys_name, dj_name, ):
        dj_group = self.dj_groups.get(name=dj_name)
        dj_members = dj_group.user_set.all()
        adder = lambda user: user.groups.add(dj_group)
        remover = lambda user: user.groups.remove(dj_group)
        return self.sync_helper(sys_name, dj_members, adder, remover, )

    def sync_many(con, what, force_print=False, ):
        changed = False
        results = {}
        for sys_name, dj_group in what:
            assert dj_group not in results
            if dj_group == "STAFF":
                results[dj_group] = con_afs.sync_staff(sys_name, )
            else:
                results[dj_group] = con_afs.sync_members(sys_name, dj_group)
            if results[dj_group]['change']: changed = True
        if changed or force_print:
            for group in results:
                print ""
                print "Results for %s:" % (group, )
                for key, value in results[group].items():
                    print "%7s:\t%s" % (key, value, )


class LDAPConnector(DjangoConnector):
    name = "LDAP"

    def __init__(self, *args, **kwargs):
        super(LDAPConnector, self).__init__(*args, **kwargs)
        self.con = ldap.initialize('ldaps://ldap-too.mit.edu')
        self.con.simple_bind_s("", "")

    def get_members(self, groupname):
        base_dn = 'ou=lists,ou=moira,dc=mit,dc=edu'
        groupfilter = ldap.filter.filter_format('(&(objectClass=group)(displayName=%s))', [groupname])
        result = self.con.search_s(base_dn, ldap.SCOPE_SUBTREE, groupfilter, )
        if len(result) > 1: print "WARNING: More than one result returned for %s" % groupname
        if len(result) < 1: print "WARNING: Only no results returned for %s" % groupname
        attrs = result[0][1]
        members = attrs['member']
        ret = set()
        for member in members:
            member_dn = ldap.dn.explode_dn(member)
            assert len(member_dn) == 5
            c_val, c_type, c_moira, c_mit, c_edu = member_dn
            assert (c_moira, c_mit, c_edu, ) == ('OU=moira', 'dc=MIT', 'dc=EDU', )
            c_val_key, c_val_sep, c_val_val = c_val.partition('=')
            if c_type == 'OU=strings':
                ret.add(('string', c_val_val, ))
            elif c_type == 'OU=users':
                ret.add(('user', c_val_val, ))
            elif c_type == 'OU=kerberos':
                ret.add(('kerberos', c_val_val, ))
            else:
                assert False, "Don't know what %s is" % (c_type, )
        return [r[1] for r in ret if r[0] == 'user']

class AFSConnector(DjangoConnector):
    name = "AFS"

    def __init__(self, *args, **kwargs):
        super(AFSConnector, self).__init__(*args, **kwargs)
        #self.login()
        self.pts = afs.pts.PTS(sec=afs.pts.PTS_ENCRYPT, cell='athena.mit.edu', )
    def login(self, ):
        if settings.KRB_KEYTAB:
            kinit_cmd = ['kinit', '-k', '-t', settings.KRB_KEYTAB, settings.KRB_PRINCIPAL, ]
            subprocess.check_call(kinit_cmd)
            subprocess.check_call(['aklog', 'athena', ])

    def get_members(self, groupname, ):
        afs_members = self.pts.getEntry("system:%s" % (groupname, )).members
        members = [ m.name for m in afs_members ]
        return members

sync_pairs = [
    ('asa-admin', 'STAFF', ),
    ('asa-admin', 'asa-ebm', ),
    ('asa-db-mit-deskworker', 'mit-deskworker', ),
    ('asa-db-mit-offices', 'mit-offices', ),
    ('asa-db-mit-sao', 'mit-sao', ),
]

def test_memberships(cons):
    for sys_name, dj_group in sync_pairs:
        for con in cons:
            members = con.get_members(sys_name)
            print "%s\t%s\t%s" % (con.name, sys_name, sorted(members))

if __name__ == '__main__':
    con_afs = AFSConnector()
    #con_ldap = LDAPConnector()
    #test_memberships([con_afs, con_ldap, ])
    con_afs.sync_many(sync_pairs)
