import datetime

from django.db import models

import reversion

import groups.models

# Create your models here.

class Space(models.Model):
    number = models.CharField(max_length=20, unique=True, )
    asa_owned = models.BooleanField(default=True, )
    notes = models.TextField(blank=True, )

    def __unicode__(self, ):
        if self.asa_owned:
            asa_str = "ASA"
        else:
            asa_str = "Non-ASA"
        return u"%s (%s)" % (self.number, asa_str)
reversion.register(Space)


class CurrentAssignmentManager(models.Manager):
    def get_query_set(self, ):
        return super(CurrentAssignmentManager, self).get_query_set().filter(
            start__lte=datetime.date.today,
            end__gte=datetime.date.today,
        )

class SpaceAssignment(models.Model):
    END_NEVER       = datetime.datetime.max

    group = models.ForeignKey(groups.models.Group)
    space = models.ForeignKey(Space)
    start = models.DateField(default=datetime.datetime.now)
    end = models.DateField(default=END_NEVER)

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


class CurrentACLEntryManager(models.Manager):
    def get_query_set(self, ):
        return super(CurrentACLEntryManager, self).get_query_set().filter(
            start__lte=datetime.datetime.now,
            end__gte=datetime.datetime.now,
        )

class SpaceAccessListEntry(models.Model):
    END_NEVER       = datetime.datetime.max

    group = models.ForeignKey(groups.models.Group)
    space = models.ForeignKey(Space)
    start = models.DateTimeField(default=datetime.datetime.now)
    end = models.DateTimeField(default=END_NEVER)

    name = models.CharField(max_length=50)
    card_number = models.CharField(max_length=20)

    objects = models.Manager()
    current = CurrentACLEntryManager()

    def expire(self, ):
        self.end_time = datetime.datetime.now()-self.EXPIRE_OFFSET
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
