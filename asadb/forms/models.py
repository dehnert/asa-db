from django.db import models

import datetime

import groups.models

class FYSM(models.Model):
    group = models.ForeignKey(groups.models.Group)
    display_name = models.CharField(max_length=50)
    year = models.IntegerField()
    website = models.URLField()
    join_url = models.URLField()
    contact_email = models.EmailField()
    description = models.TextField()
    logo = models.ImageField(upload_to='fysm/logos', )
    tags = models.ManyToManyField('FYSMTag', blank=True, )

    class Meta:
        verbose_name = "FYSM submission"

class FYSMTag(models.Model):
    name = models.CharField(max_length=10)
    slug = models.SlugField()
    blurb = models.TextField()

    def __str__(self, ):
        return self.name

    class Meta:
        verbose_name = "FYSM tag"
