import datetime
import errno
import json
import os

import ldap

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

import groups.models
from util.misc import log_and_ignore_failures, mkdir_p
import util.previews

class FYSM(models.Model):
    group = models.ForeignKey(groups.models.Group, db_index=True, )
    display_name = models.CharField(max_length=50, help_text="""Form of your name suitable for display (for example, don't end your name with ", MIT")""")
    year = models.IntegerField(db_index=True, )
    website = models.URLField()
    join_url = models.URLField(verbose_name="recruiting URL", help_text="""<p>If you have a specific web page for recruiting new members of your group, you can link to it here. It will be used as the destination for most links about your group (join link on the main listing page and when clicking on the slide, but not the "website" link on the slide page). If you do not have such a page, use your main website's URL.</p>""")
    contact_email = models.EmailField(help_text="Give an address for students interested in joining the group to email (e.g., an officers list)")
    description = models.TextField(help_text="Explain, in no more than 400 characters (including spaces), what your group does and why incoming students should get involved.")
    logo = models.ImageField(upload_to='fysm/logos', blank=True, help_text="Upload a logo (JPG, GIF, or PNG) to display on the main FYSM page as well as the group detail page. This will be scaled to be 100px wide.")
    slide = models.ImageField(upload_to='fysm/slides', blank=True, default="", help_text="Upload a slide (JPG, GIF, or PNG) to display on the group detail page. This will be scaled to be at most 600x600 pixels. We recommend making it exactly that size.")
    tags = models.CharField(max_length=100, blank=True, help_text="Specify some free-form, comma-delimited tags for your group", )
    categories = models.ManyToManyField('FYSMCategory', blank=True, help_text="Put your group into whichever of our categories seem applicable.", )
    join_preview = models.ForeignKey('PagePreview', null=True, )

    def save(self, *args, **kwargs):
        if self.join_preview is None or self.join_url != self.join_preview.url:
            self.join_preview = PagePreview.allocate_page_preview(
                filename='fysm/%d/group%d'%(self.year, self.group.pk, ),
                url=self.join_url,
            )
        super(FYSM, self).save(*args, **kwargs) # Call the "real" save() method.

    def __str__(self, ):
        return "%s (%d)" % (self.display_name, self.year, )

    class Meta:
        verbose_name = "FYSM submission"

class FYSMCategory(models.Model):
    name = models.CharField(max_length=25)
    slug = models.SlugField(unique=True, )
    blurb = models.TextField()

    def __str__(self, ):
        return self.name

    class Meta:
        verbose_name = "FYSM category"
        verbose_name_plural = "FYSM categories"
        ordering = ['name', ]

class FYSMView(models.Model):
    when = models.DateTimeField(default=datetime.datetime.now)
    fysm = models.ForeignKey(FYSM, null=True, blank=True, )
    year = models.IntegerField(null=True, blank=True, )
    page = models.CharField(max_length=20, blank=True, )
    referer = models.URLField(verify_exists=False, null=True, )
    user_agent = models.CharField(max_length=255)
    source_ip = models.IPAddressField()
    source_user = models.CharField(max_length=30, blank=True, )

    @staticmethod
    @log_and_ignore_failures(logfile=settings.LOGFILE)
    def record_metric(request, fysm=None, year=None, page=None, ):
        record = FYSMView()
        record.fysm = fysm
        record.year = year
        record.page = page
        if 'HTTP_REFERER' in request.META:
            record.referer = request.META['HTTP_REFERER']
        record.user_agent = request.META['HTTP_USER_AGENT']
        record.source_ip = request.META['REMOTE_ADDR']
        record.source_user = request.user.username
        record.save()

class PagePreview(models.Model):
    update_time = models.DateTimeField(default=datetime.datetime.utcfromtimestamp(0))
    url = models.URLField()
    image = models.ImageField(upload_to='page-previews', blank=True, )

    never_updated = datetime.datetime.utcfromtimestamp(0) # Never updated
    update_interval = datetime.timedelta(hours=23)

    def image_filename(self, ):
        return os.path.join(settings.MEDIA_ROOT, self.image.name)


    @classmethod
    def allocate_page_preview(cls, filename, url, ):
        preview = PagePreview()
        preview.update_time = cls.never_updated
        preview.url = url
        preview.image = 'page-previews/%s.jpg' % (filename, )
        image_filename = preview.image_filename()
        mkdir_p(os.path.dirname(image_filename))
        try:
            os.symlink('no-preview.jpg', image_filename)
        except OSError as exc:
            if exc.errno == errno.EEXIST:
                pass
            else: raise
        preview.save()
        return preview

    def update_preview(self, ):
        self.update_time = datetime.datetime.now()
        self.save()
        failure = util.previews.generate_webpage_preview(self.url, self.image_filename(), )
        if failure:
            self.update_time = self.never_updated
            self.save()

    @classmethod
    def previews_needing_updates(cls, interval=None, ):
        if interval is None:
            interval = cls.update_interval
        before = datetime.datetime.now() - interval
        return cls.objects.filter(update_time__lte=before)

    @classmethod
    def update_outdated_previews(cls, interval=None, ):
        previews = cls.previews_needing_updates(interval)
        now = datetime.datetime.now()
        update_list = []
        previews_dict = {}
        for preview in previews:
            update_list.append((preview.url, preview.image_filename(), ))
            previews_dict[preview.url] = preview
            preview.update_time = now
            preview.save()
        failures = util.previews.generate_webpage_previews(update_list)
        for url, msg in failures:
            print "%s: %s" % (url, msg, )
            preview = previews_dict[url]
            preview.update_time = cls.never_updated
            preview.save()


class GroupConfirmationCycle(models.Model):
    name = models.CharField(max_length=30)
    slug = models.SlugField(unique=True, )
    create_date = models.DateTimeField(default=datetime.datetime.now)
    deadlines = models.TextField(blank=True)

    def __unicode__(self, ):
        return u"GroupConfirmationCycle %d: %s" % (self.id, self.name, )

    @classmethod
    def latest(cls, ):
        return cls.objects.order_by('-create_date')[0]


class GroupMembershipUpdate(models.Model):
    update_time = models.DateTimeField(default=datetime.datetime.utcfromtimestamp(0))
    updater_name = models.CharField(max_length=30)
    updater_title = models.CharField(max_length=30, help_text="You need not hold any particular title in the group, but we like to know who is completing the form.")
    
    cycle = models.ForeignKey(GroupConfirmationCycle)
    group = models.ForeignKey(groups.models.Group, help_text="If your group does not appear in the list above, then please email asa-exec@mit.edu.", db_index=True, )
    group_email = models.EmailField(help_text="The text of the law will be automatically distributed to your members via this list, in order to comply with the law.")
    officer_email = models.EmailField()

    membership_definition = models.TextField()
    num_undergrads = models.IntegerField()
    num_grads = models.IntegerField()
    num_alum = models.IntegerField()
    num_other_affiliate = models.IntegerField(verbose_name="Num other MIT affiliates")
    num_other = models.IntegerField(verbose_name="Num non-MIT")

    membership_list = models.TextField(blank=True, help_text="Member emails on separate lines (Athena usernames where applicable)")

    email_preface = models.TextField(blank=True, help_text="If you would like, you may add text here that will preface the text of the policies when it is sent out to the group membership list provided above.")

    hazing_statement = "By checking this, I hereby affirm that I have read and understand <a href='http://web.mit.edu/asa/rules/ma-hazing-law.html'>Chapter 269: Sections 17, 18, and 19 of Massachusetts Law</a>. I furthermore attest that I have provided the appropriate address or will otherwise distribute to group members, pledges, and/or applicants, copies of Massachusetts Law 269: 17, 18, 19 and that our organization, group, or team agrees to comply with the provisions of that law. (See below for text.)"
    no_hazing = models.BooleanField(help_text=hazing_statement)

    discrimination_statement = "By checking this, I hereby affirm that I have read and understand the <a href='http://web.mit.edu/referencepubs/nondiscrimination/'>MIT Non-Discrimination Policy</a>.  I furthermore attest that our organization, group, or team agrees to not discriminate against individuals on the basis of race, color, sex, sexual orientation, gender identity, religion, disability, age, genetic information, veteran status, ancestry, or national or ethnic origin."
    no_discrimination = models.BooleanField(help_text=discrimination_statement)

    def __unicode__(self, ):
        return "GroupMembershipUpdate for %s" % (self.group, )


VALID_UNSET         = 0
VALID_AUTOVALIDATED = 10
VALID_OVERRIDDEN    = 20    # confirmed by an admin
VALID_AUTOREJECTED      = -10
VALID_HANDREJECTED      = -20
VALID_CHOICES = (
    (VALID_UNSET,           "unvalidated"),
    (VALID_AUTOVALIDATED,   "autovalidated"),
    (VALID_OVERRIDDEN,      "hand-validated"),
    (VALID_AUTOREJECTED,    "autorejected"),
    (VALID_HANDREJECTED,    "hand-rejected"),
)

class PersonMembershipUpdate(models.Model):
    update_time = models.DateTimeField(default=datetime.datetime.utcfromtimestamp(0))
    username = models.CharField(max_length=30)
    cycle = models.ForeignKey(GroupConfirmationCycle, db_index=True, )
    deleted = models.DateTimeField(default=None, null=True, blank=True, )
    valid = models.IntegerField(choices=VALID_CHOICES, default=VALID_UNSET)
    groups = models.ManyToManyField(groups.models.Group, help_text="By selecting a group here, you indicate that you are an active member of the group in question.<br>If your group does not appear in the list above, then please email asa-exec@mit.edu.<br>")

    def __unicode__(self, ):
        return "PersonMembershipUpdate for %s" % (self.username, )


class PeopleStatusLookup(models.Model):
    people = models.TextField(help_text="Enter some usernames or email addresses to look up here.")
    requestor = models.ForeignKey(User, null=True, blank=True, )
    referer = models.URLField(blank=True)
    time = models.DateTimeField(default=datetime.datetime.now)
    classified_people_json = models.TextField()
    _classified_people = None

    def ldap_classify(self, usernames, ):
        con = ldap.open('ldap-too.mit.edu')
        con.simple_bind_s("", "")
        dn = "ou=users,ou=moira,dc=mit,dc=edu"
        fields = ['uid', 'eduPersonAffiliation', 'mitDirStudentYear']

        chunk_size = 100
        username_chunks = []
        ends = range(chunk_size, len(usernames), chunk_size)
        start = 0
        end = 0
        for end in ends:
            username_chunks.append(usernames[start:end])
            start = end
        username_chunks.append(usernames[end:])
        print username_chunks

        results = []
        for chunk in username_chunks:
            filters = [ldap.filter.filter_format('(uid=%s)', [u]) for u in chunk]
            userfilter = "(|%s)" % (''.join(filters), )
            batch_results = con.search_s(dn, ldap.SCOPE_SUBTREE, userfilter, fields)
            results.extend(batch_results)

        left = set(usernames)
        undergrads = []
        grads = []
        staff = []
        secret = []
        other = []
        info = {
            'undergrads': undergrads,
            'grads': grads,
            'staff': staff,
            'secret': secret,
            'affiliate': other,
        }
        for result in results:
            username = result[1]['uid'][0]
            left.remove(username)
            affiliation = result[1].get('eduPersonAffiliation', ['secret'])[0]
            if affiliation == 'student':
                year = result[1].get('mitDirStudentYear', [None])[0]
                if year == 'G':
                    grads.append((username, None))
                elif year.isdigit():
                    undergrads.append((username, year))
                else:
                    other.append((username, year))
            else:
                info[affiliation].append((username, None, ))
        info['unknown'] = [(u, None) for u in left]
        return info

    def classify_people(self, people):
        mit_usernames = []
        alum_addresses = []
        other_mit_addresses = []
        nonmit_addresses = []

        for name in people:
            local, at, domain = name.partition('@')
            if domain.lower() == 'mit.edu' or domain == '':
                mit_usernames.append(local)
            elif domain.lower() == 'alum.mit.edu':
                alum_addresses.append((name, None))
            elif domain.endswith('.mit.edu'):
                other_mit_addresses.append((name, None))
            else:
                nonmit_addresses.append((name, None))

        results = self.ldap_classify(mit_usernames)
        results['alum'] = alum_addresses
        results['other-mit'] = other_mit_addresses
        results['non-mit'] = nonmit_addresses
        return results

    def update_classified_people(self):
        people = [p for p in [p.strip() for p in self.people.split('\n')] if p]
        self._classified_people = self.classify_people(people)
        self.classified_people_json = json.dumps(self._classified_people)
        return self._classified_people

    @property
    def classified_people(self):
        if self._classified_people is None:
            self._classified_people = json.loads(self.classified_people_json)
        return self._classified_people

    def classifications_with_descriptions(self):
        descriptions = {
            'undergrads':   'Undergraduate students (class year in parentheses)',
            'grads':        'Graduate students',
            'alum':         "Alumni Association addresses",
            'staff':        'MIT Staff (including faculty)',
            'affiliate':    'This includes some alumni, group members with Athena accounts sponsored through SAO, and many others.',
            'secret':       'People with directory information suppressed. These people have Athena accounts, but they could have any MIT affiliation, including just being a student group member.',
            'unknown':      "While this looks like an Athena account, we couldn't find it. This could be a deactivated account, or it might never have existed.",
            'other-mit':    ".mit.edu addresses that aren't @mit.edu or @alum.mit.edu.",
            'non-mit':      "Non-MIT addresses, including outside addresses of MIT students.",
        }

        names = (
            ('undergrads', 'Undergrads', ),
            ('grads', 'Grad students', ),
            ('alum', 'Alumni', ),
            ('staff', 'Staff', ),
            ('affiliate', 'Affiliates', ),
            ('secret', 'Secret', ),
            ('unknown', 'Unknown', ),
            ('other-mit', 'Other MIT addresses', ),
            ('non-mit', 'Non-MIT addresses', ),
        )

        classifications = self.classified_people
        sorted_results = []
        for k, label in names:
            sorted_results.append({
                'label': label,
                'description': descriptions[k],
                'people': sorted(classifications[k]),
            })
        return sorted_results


##########
# MIDWAY #
##########


class Midway(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField()
    date = models.DateTimeField()
    table_map = models.ImageField(upload_to='midway/maps')

    def __str__(self, ):
        return "%s" % (self.name, )

class MidwayAssignment(models.Model):
    midway = models.ForeignKey(Midway)
    location = models.CharField(max_length=20)
    group = models.ForeignKey(groups.models.Group)

    def __str__(self, ):
        return "<MidwayAssignment: %s at %s at %s>" % (self.group, self.location, self.midway, )
