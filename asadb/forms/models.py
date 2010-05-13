from django.db import models

import datetime

import groups.models

class FYSM(models.Model):
    group = models.ForeignKey(groups.models.Group)
    year = models.IntegerField()
    website = models.URLField()
    contact_email = models.EmailField()
    description = models.TextField()
    logo = models.ImageField(upload_to='fysm/logos', )
    tags = models.ManyToManyField('FYSMTags', blank=True, )

    class Meta:
        verbose_name = "FYSM submission"

class FYSMTags(models.Model):
    name = models.CharField(max_length=10)
    blurb = models.TextField()
