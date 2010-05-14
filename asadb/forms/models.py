from django.db import models

import datetime

import groups.models

class FYSM(models.Model):
    group = models.ForeignKey(groups.models.Group)
    display_name = models.CharField(max_length=50)
    year = models.IntegerField()
    website = models.URLField()
    join_url = models.URLField(help_text="If you have a specific web page for students interested in joining your group, you can link to it here. If you leave this blank it will default to your website.")
    contact_email = models.EmailField(help_text="Give an address for students interested in joining the group to email (e.g., an officers list)")
    description = models.TextField(help_text="Explain in about three or four sentences what your group does and why incoming freshmen should get involved.")
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
