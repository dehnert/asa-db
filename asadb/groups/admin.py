import groups.models
from django.contrib import admin

class GroupAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'abbreviation',
        'activity_category',
        'officer_email',
        'main_account_id',
        'funding_account_id',
        'athena_locker',
        'update_date',
        'updater',
    )
    list_display_links = ('id', 'name', )
    search_fields = [ 'id', 'name', 'abbreviation', 'officer_email', 'athena_locker', ]

class ActivityCategoryAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
    )
    list_display_links = ('id', 'name', )

admin.site.register(groups.models.Group, GroupAdmin)
admin.site.register(groups.models.ActivityCategory, ActivityCategoryAdmin)
