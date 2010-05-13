from django.db import models

# Create your models here.
class Group(models.Model):
    name = models.CharField(max_length=50)
    abbreviation = models.CharField(max_length=10, blank=True)
    description = models.TextField()
    activity_category = models.ForeignKey('ActivityCategory', null=True, blank=True, )
    website_url = models.URLField()
    constitution_url = models.URLField()
    meeting_times = models.TextField(blank=True)
    advisor_name = models.CharField(max_length=50, blank=True)
    num_undergrads = models.IntegerField(null=True, blank=True, )
    num_grads = models.IntegerField(null=True, blank=True, )
    num_community = models.IntegerField(null=True, blank=True, )
    num_other = models.IntegerField(null=True, blank=True, )
    group_email = models.EmailField()
    officer_email = models.EmailField()
    main_account_id = models.IntegerField(null=True, blank=True, )
    funding_account_id = models.IntegerField(null=True, blank=True, )
    athena_locker = models.CharField(max_length=14)
    recognition_date = models.DateField()
    update_date = models.DateTimeField()
    updater = models.CharField(max_length=30) # match Django username field

    def __str__(self, ):
        return self.name

    class Meta:
        ordering = ('name', )

class ActivityCategory(models.Model):
    name = models.CharField(max_length=50)
