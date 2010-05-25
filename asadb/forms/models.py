from django.db import models

import datetime
import os, errno

import settings
import groups.models
from util.misc import log_and_ignore_failures, mkdir_p
import util.previews

class FYSM(models.Model):
    group = models.ForeignKey(groups.models.Group)
    display_name = models.CharField(max_length=50)
    year = models.IntegerField()
    website = models.URLField()
    join_url = models.URLField(help_text="If you have a specific web page for students interested in joining your group, you can link to it here. This page will be snapshotted daily, and displayed on your group's FYSM detail page. It should first update in the next fifteen minutes.")
    contact_email = models.EmailField(help_text="Give an address for students interested in joining the group to email (e.g., an officers list)")
    description = models.TextField(help_text="Explain in about three or four sentences what your group does and why incoming freshmen should get involved.")
    logo = models.ImageField(upload_to='fysm/logos', blank=True, )
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
