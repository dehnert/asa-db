import groups.models
from django.contrib import admin
from reversion.admin import VersionAdmin

class GroupAdmin(VersionAdmin):
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

class OfficerRoleAdmin(VersionAdmin):
    list_display = (
        'id',
        'display_name',
        'slug',
        'max_count',
    )
    list_display_links = ('id', 'display_name', 'slug', )
    prepopulated_fields = {"slug": ("display_name",)}

class OfficeHolderAdmin(VersionAdmin):
    list_display = (
        'id',
        'person',
        'role',
        'group',
        'start_time', 'end_time',
    )
    list_display_links = (
        'id',
        'person',
        'role',
        'group',
        'start_time', 'end_time',
    )
    search_fields = (
        'id',
        'person',
        'role__display_name', 'role__slug',
        'group__name', 'group__abbreviation',
        'start_time', 'end_time',
    )

class ActivityCategoryAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
    )
    list_display_links = ('id', 'name', )

admin.site.register(groups.models.Group, GroupAdmin)
admin.site.register(groups.models.ActivityCategory, ActivityCategoryAdmin)
admin.site.register(groups.models.OfficerRole, OfficerRoleAdmin)
admin.site.register(groups.models.OfficeHolder, OfficeHolderAdmin)
