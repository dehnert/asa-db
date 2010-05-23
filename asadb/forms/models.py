from django.db import models

import datetime

import settings
import groups.models
from util.misc import log_and_ignore_failures

class FYSM(models.Model):
    group = models.ForeignKey(groups.models.Group)
    display_name = models.CharField(max_length=50)
    year = models.IntegerField()
    website = models.URLField()
    join_url = models.URLField(help_text="If you have a specific web page for students interested in joining your group, you can link to it here. If you leave this blank it will default to your website.")
    contact_email = models.EmailField(help_text="Give an address for students interested in joining the group to email (e.g., an officers list)")
    description = models.TextField(help_text="Explain in about three or four sentences what your group does and why incoming freshmen should get involved.")
    logo = models.ImageField(upload_to='fysm/logos', blank=True, )
    tags = models.CharField(max_length=100, blank=True, help_text="Specify some free-form, comma-delimited tags for your group", )
    categories = models.ManyToManyField('FYSMCategory', blank=True, help_text="Put your group into whichever of our categories seem applicable.", )

    class Meta:
        verbose_name = "FYSM submission"

class FYSMCategory(models.Model):
    name = models.CharField(max_length=10)
    slug = models.SlugField()
    blurb = models.TextField()

    def __str__(self, ):
        return self.name

    class Meta:
        verbose_name = "FYSM category"
        verbose_name_plural = "FYSM categories"

class FYSMView(models.Model):
    fysm = models.ForeignKey(FYSM, blank=True, )
    year = models.IntegerField(null=True, blank=True, )
    page = models.CharField(max_length=20, blank=True, )
    referer = models.URLField(verify_exists=False)
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
        record.referer = request.META['HTTP_REFERER']
        record.user_agent = request.META['HTTP_USER_AGENT']
        record.source_ip = request.META['REMOTE_ADDR']
        record.source_user = request.user.username
        record.save()
