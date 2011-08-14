from django.db import models
from django.contrib.auth.models import User

import datetime

import settings

# Create your models here.
class Group(models.Model):
    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=10, blank=True)
    description = models.TextField()
    activity_category = models.ForeignKey('ActivityCategory', null=True, blank=True, )
    group_class = models.ForeignKey('GroupClass')
    group_status = models.ForeignKey('GroupStatus')
    group_funding = models.ForeignKey('GroupFunding', null=True, blank=True, )
    website_url = models.URLField()
    constitution_url = models.CharField(max_length=200, blank=True)
    meeting_times = models.TextField(blank=True)
    advisor_name = models.CharField(max_length=100, blank=True)
    num_undergrads = models.IntegerField(null=True, blank=True, )
    num_grads = models.IntegerField(null=True, blank=True, )
    num_community = models.IntegerField(null=True, blank=True, )
    num_other = models.IntegerField(null=True, blank=True, )
    group_email = models.EmailField(blank=True, )
    officer_email = models.EmailField()
    main_account_id = models.IntegerField(null=True, blank=True, )
    funding_account_id = models.IntegerField(null=True, blank=True, )
    athena_locker = models.CharField(max_length=20, blank=True)
    recognition_date = models.DateField()
    update_date = models.DateTimeField(editable=False, )
    updater = models.CharField(max_length=30, editable=False, ) # match Django username field
    _updater_set = False

    def update_string(self, ):
        updater = self.updater or "unknown"
        return "%s by %s" % (self.update_date.strftime(settings.DATETIME_FORMAT_PYTHON), updater, )

    def set_updater(self, who):
        if hasattr(who, 'username'):
            self.updater = who.username
        else:
            self.updater = who
        self._updater_set = True

    def save(self, ):
        if not self._updater_set:
            self.updater = None
        self.update_date = datetime.datetime.now()
        super(Group, self).save()

    def officers(self, role=None, person=None, as_of="now",):
        """Get the set of people holding some office.

        If None is passed for role, person, or as_of, that field will not
        be constrained. If as_of is "now" (default) the status will be
        required to be current. If any of the three parameters are set
        to another value, the corresponding filter will be applied.
        """
        office_holders = OfficeHolder.objects.filter(group=self,)
        if role:
            if isinstance(role, str):
                office_holders = office_holders.filter(role__slug=role)
            else:
                office_holders = office_holders.filter(role=role)
        if person:
            office_holders = office_holders.filter(person=person)
        if as_of:
            if as_of == "now": as_of = datetime.datetime.now()
            office_holders = office_holders.filter(start_time__lte=as_of, end_time__gte=as_of)
        return office_holders

    def __str__(self, ):
        return self.name

    class Meta:
        ordering = ('name', )
        permissions = (
            ('view_group_private_info', 'View private group information'),
            # ability to update normal group info or people
            # this is weaker than change_group, which is the built-in
            # permission that controls the admin interface
            ('admin_group', 'Administer basic group information'),
            ('view_signatories', 'View signatory information for all groups'),
        )


class OfficerRole(models.Model):
    UNLIMITED = 10000

    display_name = models.CharField(max_length=50)
    slug = models.SlugField()
    description = models.TextField()
    max_count = models.IntegerField(default=UNLIMITED, help_text='Maximum number of holders of this role. Use %d for no limit.' % UNLIMITED)
    require_student = models.BooleanField(default=False)
    grant_user = models.ForeignKey(User, null=True, blank=True, )

    def max_count_str(self, ):
        if self.max_count == self.UNLIMITED:
            return "unlimited"
        else:
            return str(self.max_count)

    def __str__(self, ):
        return self.display_name

    @classmethod
    def getGrantUsers(cls, roles):
        ret = set([role.grant_user for role in roles])
        if None in ret: ret.remove(None)
        return ret

    @classmethod
    def retrieve(cls, slug, ):
        return cls.objects.get(slug=slug)


class OfficeHolder_CurrentManager(models.Manager):
    def get_query_set(self, ):
        return super(OfficeHolder_CurrentManager, self).get_query_set().filter(
            start_time__lte=datetime.datetime.now,
            end_time__gte=datetime.datetime.now,
        )

class OfficeHolder(models.Model):
    EXPIRE_OFFSET   = datetime.timedelta(seconds=1)
    END_NEVER       = datetime.datetime.max

    person = models.CharField(max_length=30)
    role = models.ForeignKey('OfficerRole')
    group = models.ForeignKey('Group')
    start_time = models.DateTimeField(default=datetime.datetime.now)
    end_time = models.DateTimeField(default=datetime.datetime.max)

    objects = models.Manager()
    current_holders = OfficeHolder_CurrentManager()

    def expire(self, ):
        self.end_time = datetime.datetime.now()-self.EXPIRE_OFFSET
        self.save()

    def __str__(self, ):
        return "<OfficeHolder: person=%s, role=%s, group=%s, start_time=%s, end_time=%s>" % (
            self.person, self.role, self.group, self.start_time, self.end_time, )

    def __repr__(self, ):
        return str(self)


class PerGroupAuthz:
    supports_anonymous_user = True
    supports_inactive_user = True
    supports_object_permissions = True

    def authenticate(self, username=None, password=None, ):
        return None # we don't do authn
    def get_user(user_id, ):
        return None # we don't do authn

    def has_perm(self, user_obj, perm, obj=None, ):
        print "Checking user %s for perm %s on obj %s" % (user_obj, perm, obj)
        if not user_obj.is_active:
            return False
        if not user_obj.is_authenticated():
            return False
        if obj is None:
            return False
        # Great, we're active, authenticated, and not in a recursive call
        # Check that we've got a reasonable object
        if getattr(user_obj, 'is_system', False):
            return False
        if isinstance(obj, Group):
            # Now we can do the real work
            holders = obj.officers(person=user_obj.username).select_related('role__grant_user')
            sys_users = OfficerRole.getGrantUsers([holder.role for holder in holders])
            for sys_user in sys_users:
                sys_user.is_system = True
                if sys_user.has_perm(perm):
                    print "While checking user %s for perm %s on obj %s: implicit user %s has perms" % (user_obj, perm, obj, sys_user, )
                    return True
        print "While checking user %s for perm %s on obj %s: no perms found (implicit: %s)" % (user_obj, perm, obj, sys_users)
        return False



class ActivityCategory(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self, ):
        return self.name

    class Meta:
        verbose_name_plural = "activity categories"


class GroupClass(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True, )
    description = models.TextField()
    gets_publicity = models.BooleanField(help_text="Gets publicity resources such as FYSM or Activities Midway")

    def __str__(self, ):
        return self.name

    class Meta:
        verbose_name_plural = "group classes"


class GroupStatus(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True, )
    description = models.TextField()
    is_active = models.BooleanField(default=True, help_text="This status represents an active group")

    def __str__(self, ):
        active = ""
        if not self.is_active:
            active = " (inactive)"
        return "%s%s" % (self.name, active, )

    class Meta:
        verbose_name_plural= "group statuses"


class GroupFunding(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True, )
    contact_email = models.EmailField()
    funding_list = models.CharField(max_length=32, blank=True, help_text="List that groups receiving funding emails should be on. The database will attempt to make sure that ONLY those groups are on it.")

    def __str__(self, ):
        return "%s (%s)" % (self.name, self.contact_email, )


class AthenaMoiraAccount_ActiveManager(models.Manager):
    def get_query_set(self, ):
        return super(AthenaMoiraAccount_ActiveManager, self).get_query_set().filter(del_date=None)

class AthenaMoiraAccount(models.Model):
    username = models.CharField(max_length=8)
    mit_id = models.CharField(max_length=15)
    first_name      = models.CharField(max_length=45)
    last_name       = models.CharField(max_length=45)
    account_class   = models.CharField(max_length=10)
    mutable         = models.BooleanField(default=True)
    add_date        = models.DateField(help_text="Date when this person was added to the dump.", )
    del_date        = models.DateField(help_text="Date when this person was removed from the dump.", blank=True, null=True, )
    mod_date        = models.DateField(help_text="Date when this person's record was last changed.", blank=True, null=True, )

    objects = models.Manager()
    active_accounts = AthenaMoiraAccount_ActiveManager()

    def is_student(self, ):
        # XXX: Is this... right?
        return self.account_class == 'G' or self.account_class.isdigit()

    def __str__(self, ):
        if self.mutable:
            mutable_str = ""
        else:
            mutable_str = " (immutable)"
        return "<AthenaMoiraAccount: username=%s name='%s, %s' account_class=%s%s>" % (
            self.username, self.last_name, self.first_name,
            self.account_class, mutable_str,
        )

    def __repr__(self, ):
        return str(self)

    class Meta:
        verbose_name = "Athena (Moira) account"
