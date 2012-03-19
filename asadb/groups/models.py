from django.db import models
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
import reversion

import datetime
import filecmp
import mimetypes
import os
import re
import shutil
import urllib

import settings

# Create your models here.

class ActiveGroupManager(models.Manager):
    def get_query_set(self, ):
        return super(ActiveGroupManager, self).get_query_set().filter(
            group_status__slug='active',
        )

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
    group_email = models.EmailField(verbose_name="group email list", blank=True, )
    officer_email = models.EmailField(verbose_name="officers' email list")
    main_account_id = models.IntegerField(null=True, blank=True, )
    funding_account_id = models.IntegerField(null=True, blank=True, )
    athena_locker = models.CharField(max_length=20, blank=True, help_text="Often, this will appear in your group's URL --- http://web.mit.edu/SOME_VARIANT_OF_GROUP_NAME/, http://www.mit.edu/~SOME_VARIANT_OF_GROUP_NAME/ and http://SOME_VARIANT_OF_GROUP_NAME.scripts.mit.edu/ all correspond to a locker name of SOME_VARIANT_OF_GROUP_NAME. Also, you can probably find this in your entry in the old database.")
    recognition_date = models.DateTimeField()
    update_date = models.DateTimeField(editable=False, )
    updater = models.CharField(max_length=30, editable=False, null=True, ) # match Django username field
    _updater_set = False

    objects = models.Manager()
    active_groups = ActiveGroupManager()

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

    def viewable_notes(self, user):
        return GroupNote.viewable_notes(self, user)

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

    def slug(self, ):
        return slugify(self.name)

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
            ('recognize_nge', 'Recognize Non-Group Entity'),
            ('recognize_group', 'Recognize groups'),
        )
reversion.register(Group)


constitution_dir = os.path.join(settings.SITE_ROOT, '..', 'constitutions')

class GroupConstitution(models.Model):
    group = models.ForeignKey(Group, unique=True, )
    source_url = models.URLField()
    dest_file = models.CharField(max_length=100)
    last_update = models.DateTimeField(help_text='Last time when this constitution actually changed.')
    last_download = models.DateTimeField(help_text='Last time we downloaded this constitution to see if it had changed.')
    failure_date = models.DateTimeField(null=True, blank=True, default=None, help_text='Time this URL started failing to download. (Null if currently working.)')
    status_msg = models.CharField(max_length=20)
    failure_reason = models.CharField(max_length=100, blank=True, default="")

    def update(self, ):
        url = self.source_url
        success = None
        old_success = (self.failure_date is None)
        if url:
            url_opener = urllib.FancyURLopener()
            now = datetime.datetime.now()
            try:
                tmp_path, headers = url_opener.retrieve(url)
            except IOError:
                self.failure_date = now
                self.save()
                success = False
                self.status_msg = "retrieval failed"
                self.failure_reason = self.status_msg
                return (success, self.status_msg, old_success, )
            if tmp_path == url:
                mover = shutil.copyfile
            else:
                mover = shutil.move
            save_filename = self.compute_filename(tmp_path, headers, )
            dest_path = self.path_from_filename(self.dest_file)
            if save_filename != self.dest_file:
                if self.dest_file: os.remove(dest_path)
                mover(tmp_path, self.path_from_filename(save_filename))
                self.dest_file = save_filename
                self.last_update = now
                self.status_msg = "new path"
            else:
                if filecmp.cmp(tmp_path, dest_path, shallow=False, ):
                    self.status_msg = "no change"
                else:
                    # changed
                    mover(tmp_path, dest_path)
                    self.last_update = now
                    self.status_msg = "updated in place"
            self.last_download = now
            self.failure_date = None
            self.failure_reason = ""
            self.save()
            success = True
        else:
            success = False
            self.status_msg = "no url"
            self.failure_reason = self.status_msg
        return (success, self.status_msg, old_success, )

    def compute_filename(self, tmp_path, headers, ):
        slug = self.group.slug()
        basename, fileext = os.path.splitext(tmp_path)
        if fileext:
            ext = fileext
        else:
            if headers.getheader('Content-Type'):
                mimeext = mimetypes.guess_extension(headers.gettype())
                if mimeext:
                    ext = mimeext
                else:
                    ext = ''
            else:
                ext = ''
        return "%04d-%s%s" % (self.group.pk, slug, ext, )

    def path_from_filename(self, filename):
        path = os.path.join(constitution_dir, filename)
        return path

    def webstat(self, ):
        url = self.source_url
        if url:
            try:
                stream = urllib.urlopen(self.source_url)
                return stream.getcode()
            except:
                return "IOError"
        else:
            return "no-url"

reversion.register(GroupConstitution)

GROUP_STARTUP_STAGE_SUBMITTED = 10
GROUP_STARTUP_STAGE_APPROVED = 20
GROUP_STARTUP_STAGE_REJECTED = -10
GROUP_STARTUP_STAGE = (
    (GROUP_STARTUP_STAGE_SUBMITTED,     'submitted'),
    (GROUP_STARTUP_STAGE_APPROVED,      'approved'),
    (GROUP_STARTUP_STAGE_REJECTED,      'rejected'),
)


class GroupStartup(models.Model):
    group = models.ForeignKey(Group)
    stage = models.IntegerField(choices=GROUP_STARTUP_STAGE)
    submitter = models.CharField(max_length=30, editable=False, )
    create_officer_list = models.BooleanField()
    create_group_list = models.BooleanField()
    create_athena_locker = models.BooleanField()
    president_name = models.CharField(max_length=50)
    president_kerberos = models.CharField(max_length=8)
    treasurer_name = models.CharField(max_length=50)
    treasurer_kerberos = models.CharField(max_length=8)
reversion.register(GroupStartup)


class GroupNote(models.Model):
    author = models.CharField(max_length=30, ) # match Django username field
    timestamp = models.DateTimeField(default=datetime.datetime.now, editable=False, )
    body = models.TextField()
    acl_read_group = models.BooleanField(default=True, help_text='Can the group read this note')
    acl_read_offices = models.BooleanField(default=True, help_text='Can "offices" that interact with groups (SAO, CAC, and funding boards) read this note')
    group = models.ForeignKey(Group)

    def __str__(self, ):
        return "Note by %s on %s" % (self.author, self.timestamp, )

    @classmethod
    def viewable_notes(cls, group, user):
        notes = cls.objects.filter(group=group)
        if not user.has_perm('groups.view_note_all'):
            q = models.Q(pk=0)
            if user.has_perm('groups.view_note_group', group):
                q |= models.Q(acl_read_group=True)
            if user.has_perm('groups.view_note_office'):
                q |= models.Q(acl_read_offices=True)
            notes = notes.filter(q)
        return notes

    class Meta:
        permissions = (
            ('view_note_group',     'View notes intended for the group to see', ),
            ('view_note_office',    'View notes intended for "offices" to see', ),
            ('view_note_all',       'View all notes', ),
        )
reversion.register(GroupNote)


class OfficerRole(models.Model):
    UNLIMITED = 10000

    display_name = models.CharField(max_length=50)
    slug = models.SlugField()
    description = models.TextField()
    max_count = models.IntegerField(default=UNLIMITED, help_text='Maximum number of holders of this role. Use %d for no limit.' % UNLIMITED)
    require_student = models.BooleanField(default=False)
    grant_user = models.ForeignKey(User, null=True, blank=True,
        limit_choices_to={ 'username__endswith': '@SYSTEM'})
    publicly_visible = models.BooleanField(default=True, help_text='Can everyone see the holders of this office.')

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
reversion.register(OfficerRole)


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

    def format_person(self, ):
        return AthenaMoiraAccount.try_format_by_username(self.person, )

    def expire(self, ):
        self.end_time = datetime.datetime.now()-self.EXPIRE_OFFSET
        self.save()

    def __str__(self, ):
        return "<OfficeHolder: person=%s, role=%s, group=%s, start_time=%s, end_time=%s>" % (
            self.person, self.role, self.group, self.start_time, self.end_time, )

    def __repr__(self, ):
        return str(self)
reversion.register(OfficeHolder)


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
            # Having the unqualified perm means that you should have it
            # on any object
            if user_obj.has_perm(perm):
                return True
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

    def format(self, ):
        return "%s %s <%s>" % (self.first_name, self.last_name, self.username, )

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

    @classmethod
    def try_format_by_username(cls, username):
        try:
            moira = AthenaMoiraAccount.objects.get(username=username)
            return moira.format()
        except AthenaMoiraAccount.DoesNotExist:
            return "%s (name not available)" % (username)

    class Meta:
        verbose_name = "Athena (Moira) account"
