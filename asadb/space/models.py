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

class SpaceAssignment(models.Model):
    END_NEVER       = datetime.datetime.max

    group = models.ForeignKey(groups.models.Group)
    space = models.ForeignKey(Space)
    start = models.DateField(default=datetime.datetime.now)
    end = models.DateField(default=END_NEVER)

    notes = models.TextField(blank=True, )
    locker_num = models.CharField(max_length=10, blank=True, help_text='Locker number. If set, will use the "locker-access" OfficerRole to maintain access. If unset/blank, uses "office-access" and SpaceAccessListEntry for access.')

    def expire(self, ):
        self.end_time = datetime.datetime.now()-self.EXPIRE_OFFSET
        self.save()

class SpaceAccessListEntry(models.Model):
    END_NEVER       = datetime.datetime.max

    group = models.ForeignKey(groups.models.Group)
    space = models.ForeignKey(Space)
    start = models.DateTimeField(default=datetime.datetime.now)
    end = models.DateTimeField(default=END_NEVER)

    name = models.CharField(max_length=50)
    card_number = models.CharField(max_length=20)

    def expire(self, ):
        self.end_time = datetime.datetime.now()-self.EXPIRE_OFFSET
        self.save()
