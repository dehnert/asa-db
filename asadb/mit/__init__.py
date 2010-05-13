from django.contrib.auth.middleware import RemoteUserMiddleware
from django.contrib.auth.backends import RemoteUserBackend
from django.contrib import auth
from django.core.exceptions import ObjectDoesNotExist

def zephyr(msg, clas='remit', instance='log', rcpt='adehnert',):
    import os
    os.system("zwrite -d -c '%s' -i '%s' '%s' -m '%s'" % (clas, instance, rcpt, msg, ))

class ScriptsRemoteUserMiddleware(RemoteUserMiddleware):
    header = 'SSL_CLIENT_S_DN_Email'

class ScriptsRemoteUserBackend(RemoteUserBackend):
    def clean_username(self, username, ):
        if '@' in username:
            name, domain = username.split('@')
            assert domain.upper() == 'MIT.EDU'
            return name
        else:
            return username
    def configure_user(self, user, ):
        username = user.username
        import ldap
        con = ldap.open('ldap.mit.edu')
        con.simple_bind_s("", "")
        dn = "dc=mit,dc=edu"
        fields = ['cn', 'sn', 'givenName', 'mail', ]
        result = con.search_s('dc=mit,dc=edu', ldap.SCOPE_SUBTREE, 'uid=%s'%username, fields)
        if len(result) == 1:
            user.first_name = result[0][1]['givenName'][0]
            user.last_name = result[0][1]['sn'][0]
            user.email = result[0][1]['mail'][0]
            try:
                user.groups.add(auth.models.Group.objects.get(name='mit'))
            except ObjectDoesNotExist:
                print "Failed to retrieve mit group"
            user.save()
        try:
            user.groups.add(auth.models.Group.objects.get(name='autocreated'))
        except ObjectDoesNotExist:
            print "Failed to retrieve autocreated group"
        return user
