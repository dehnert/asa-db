#!/usr/bin/python

import ldap
import ldap.dn
import ldap.filter
import os
import sys

class LDAPConnector(object):
    def __init__(self, ):
        self.con = ldap.initialize('ldaps://ldap-too.mit.edu')
        self.con.simple_bind_s("", "")

    def get_members_ldap(self, groupname):
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
        return ret

if __name__ == '__main__':
    con = LDAPConnector()
    for listname in sys.argv[1:]:
        members = con.get_members_ldap(listname)
        print "%s\t%s" % (listname, members)
