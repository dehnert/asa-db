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
    list_filter = [ 'activity_category', ]
    date_hierarchy = 'update_date'
    search_fields = [ 'id', 'name', 'abbreviation', 'officer_email', 'athena_locker', ]

class OfficerRoleAdmin(VersionAdmin):
    list_display = (
        'id',
        'display_name',
        'slug',
        'max_count',
        'require_student',
        'grant_user',
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

class Admin_AthenaMoiraAccount(admin.ModelAdmin):
    list_display = (
        'id',
        'username',
        'mit_id',
        'first_name',
        'last_name',
        'account_class',
        'mutable',
        'add_date',
        'del_date',
        'mod_date',
    )
    list_display_links = ( 'id', 'username', )
    search_fields = ( 'username', 'mit_id', 'first_name', 'last_name', 'account_class', )

admin.site.register(groups.models.Group, GroupAdmin)
admin.site.register(groups.models.ActivityCategory, ActivityCategoryAdmin)
admin.site.register(groups.models.OfficerRole, OfficerRoleAdmin)
admin.site.register(groups.models.OfficeHolder, OfficeHolderAdmin)
admin.site.register(groups.models.AthenaMoiraAccount, Admin_AthenaMoiraAccount)
