import collections
import datetime

from django.db import models
from django.db.models import Q

import reversion

import groups.models

EXPIRE_OFFSET   = datetime.timedelta(seconds=1)

class Space(models.Model):
    number = models.CharField(max_length=20, unique=True, )
    asa_owned = models.BooleanField(default=True, )
    merged_acl = models.BooleanField(default=False, help_text="Does this room have a single merged ACL, that combines all groups together, or CAC maintain a separate ACL per-group? Generally, the shared storage offices get a merged ACL and everything else doesn't.")
    notes = models.TextField(blank=True, )

    def __unicode__(self, ):
        if self.asa_owned:
            asa_str = "ASA"
        else:
            asa_str = "Non-ASA"
        return u"%s (%s)" % (self.number, asa_str)

    def build_access(self, time=None, group=None, ):
        """Assemble a list of who had access to this Space.

        time:
            optional; indicate that you want access as of a particular time.
            If omitted, uses the present.
        group:
            optional; indicates that you want access via a particular group.
            If omitted, finds access via any group.

        Return value:
            tuple (access, assignments, aces, errors)
            access is the main field that matters, but the others are potentially useful supplementary information

            access:
                Group.pk -> (ID -> Set name)
                Indicates who has access. Grouped by group and ID number.
                Usually, the sets will each have one member, but ID 999999999 is decently likely to have several.
                The SpaceAccessListEntrys will be filtered to reflect assignments as of that time.
            access_by_id:
                ID -> (Name -> (Set Group.pk))
                Indicates who has access. Grouped by ID number and name.
                Usually, each ID dict will have one member, but ID 999999999 is, again, likely to have several.
                This is intended for rooms that have one access list (e.g., W20-437 and W20-441)
            assignments:
                [SpaceAssignment]
                QuerySet of all SpaceAssignments involving the space and group at the time
            aces:
                [SpaceAccessListEntry]
                QuerySet of all SpaceAccessListEntrys involving the space and group at the time.
                This is not filtered for the ace's group having a relevant SpaceAssignment.
            errors:
                [String]
                errors/warnings that occurred.
                Includes messages about groups no longer having access.
        """

        if time is None:
            time = datetime.datetime.now()
        errors = []
        time_q = Q(end__gte=time, start__lte=time)
        assignments = SpaceAssignment.objects.filter(time_q, space=self)
        aces = SpaceAccessListEntry.objects.filter(time_q, space=self)
        if group:
            assignments = assignments.filter(group=group)
            aces = aces.filter(group=group)
        access = {}    # Group.pk -> (ID -> Set name)
        # ID -> (Name -> (Set Group.pk))
        access_by_id = collections.defaultdict(lambda: collections.defaultdict(set))
        for assignment in assignments:
            if assignment.group.pk not in access:
                access[assignment.group.pk] = collections.defaultdict(set)
        for ace in aces:
            if ace.group.pk in access:
                access[ace.group.pk][ace.card_number].add(ace.name)
                access_by_id[ace.card_number][ace.name].add(ace.group.pk)
            else:
                # This group appears to no longer have access...
                errors.append("Group %s no longer has access to %s, but has live ACEs." % (ace.group, self, ))
        return access, access_by_id, assignments, aces, errors

reversion.register(Space)


class CurrentAssignmentManager(models.Manager):
    def get_query_set(self, ):
        return super(CurrentAssignmentManager, self).get_query_set().filter(
            start__lte=datetime.date.today,
            end__gte=datetime.date.today,
        )

class SpaceAssignment(models.Model):
    END_NEVER       = datetime.datetime.max

    group = models.ForeignKey(groups.models.Group, db_index=True, )
    space = models.ForeignKey(Space, db_index=True, )
    start = models.DateField(default=datetime.datetime.now, db_index=True, )
    end = models.DateField(default=END_NEVER, db_index=True, )

    notes = models.TextField(blank=True, )
    locker_num = models.CharField(max_length=10, blank=True, help_text='Locker number. If set, will use the "locker-access" OfficerRole to maintain access. If unset/blank, uses "office-access" and SpaceAccessListEntry for access.')

    objects = models.Manager()
    current = CurrentAssignmentManager()

    def expire(self, ):
        self.end_time = datetime.datetime.now()-self.EXPIRE_OFFSET
        self.save()

    def is_locker(self, ):
        return bool(self.locker_num)

    def __unicode__(self, ):
        return u"<SpaceAssignment group=%s space=%s locker=%s start=%s end=%s>" % (
            self.group,
            self.space,
            self.locker_num,
            self.start,
            self.end,
        )


groups.models.filter_registry.register(
    category='space',
    slug='space:owners',
    name='Space owners',
    desc='Groups with space',
    qs_thunk=lambda: SpaceAssignment.current.values('group'),
)

def building_filter(building):
    building_assignments = SpaceAssignment.current.filter(
        space__number__startswith="%s-" % (building, ),
    )
    owners = groups.models.Group.objects.filter(
        pk__in=building_assignments.values('group'),
    )
    return owners

groups.models.filter_registry.register(
    category='space',
    slug='space:w20',
    name='W20 owners',
    desc='Owners of W20 space',
    qs_thunk=lambda: building_filter('W20'),
)
groups.models.filter_registry.register(
    category='space',
    slug='space:walker',
    name='Walker owners',
    desc='Owners of Walker space',
    qs_thunk=lambda: building_filter('50'),
)

class CurrentACLEntryManager(models.Manager):
    def get_query_set(self, ):
        return super(CurrentACLEntryManager, self).get_query_set().filter(
            start__lte=datetime.datetime.now,
            end__gte=datetime.datetime.now,
        )

def now_offset():
    return datetime.datetime.now()-EXPIRE_OFFSET

class SpaceAccessListEntry(models.Model):
    END_NEVER       = datetime.datetime.max

    group = models.ForeignKey(groups.models.Group, db_index=True, )
    space = models.ForeignKey(Space, db_index=True, )
    start = models.DateTimeField(default=now_offset, db_index=True, )
    end = models.DateTimeField(default=END_NEVER, db_index=True, )

    name = models.CharField(max_length=50)
    card_number = models.CharField(max_length=20, verbose_name="MIT ID", help_text="MIT ID number (as printed on, eg, the relevant ID card)")

    objects = models.Manager()
    current = CurrentACLEntryManager()

    def expire(self, ):
        self.end = now_offset()
        self.save()

    def format_name(self, ):
        return u"%s (%s)" % (self.name, self.card_number, )

    def __unicode__(self, ):
        return u"<SpaceAccessListEntry group=%s space=%s name=%s start=%s end=%s>" % (
            self.group,
            self.space,
            self.name,
            self.start,
            self.end,
        )
