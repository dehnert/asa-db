import groups.models
from django.contrib import admin

class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbreviation', 'officer_email', 'main_account_id', 'funding_account_id', 'athena_locker', 'update_date', 'updater', )

admin.site.register(groups.models.Group, GroupAdmin)
