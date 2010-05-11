from django.db import models

# Create your models here.
class Group(models.Model):
    name = models.CharField(max_length=50)
    abbreviation = models.CharField(max_length=10, blank=True)
    description = models.TextField()
    activity_category = models.ForeignKey('ActivityCategory')
    website_url = models.URLField()
    constitution_url = models.URLField()
    meeting_times = models.TextField(blank=True)
    advisor_name = models.CharField(max_length=50, blank=True)
    num_undergrads = models.IntField()
    num_grads = models.IntField()
    num_community = models.IntField()
    num_other = models.IntField()
    group_email = models.EmailField()
    officer_email = models.EmailField()
    main_account_id = models.IntField()
    funding_account_id = models.IntField()
    athena_locker = models.CharField(max_length=14)
    recognition_date = models.DateField()
    update_date = models.DateTimeField()
    updater = models.CharField(max_length=30) # match Django username field

class ActivityCategory(models.Model):
    name = models.CharField(max_length=50)
