from django.contrib import admin

from reversion.admin import VersionAdmin

import groups.models
import util.admin

class GroupAdmin(VersionAdmin):
    list_max_show_all = 1000
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
    list_filter = [
        'activity_category',
        'group_class',
        'group_status',
        'group_funding',
    ]
    date_hierarchy = 'update_date'
    search_fields = [ 'id', 'name', 'abbreviation', 'officer_email', 'athena_locker', ]
admin.site.register(groups.models.Group, GroupAdmin)


class Admin_GroupConstitution(VersionAdmin):
    list_display = (
        'pk',
        'group',
        'source_url',
        'dest_file',
        'last_update',
        'last_download',
        'failure_date',
    )
admin.site.register(groups.models.GroupConstitution, Admin_GroupConstitution)


class Admin_GroupStartup(VersionAdmin):
    list_display = (
        'id',
        'group',
        'stage',
        'submitter',
        'president_kerberos',
        'create_officer_list',
        'create_group_list',
        'create_athena_locker',
    )
    list_display_links = ('id', 'group', )
    search_fields = [ 'group__name', 'group__abbreviation', 'submitter', 'president_kerberos', ]
admin.site.register(groups.models.GroupStartup, Admin_GroupStartup)

class Admin_GroupNote(VersionAdmin):
    list_display = (
        'pk',
        'author',
        'timestamp',
        'acl_read_group',
        'acl_read_offices',
        'group',
    )
    list_display_links = ('pk', 'timestamp', )
    list_filter = [
        'acl_read_group',
        'acl_read_offices',
    ]
    date_hierarchy = 'timestamp'
    search_fields = [
        'author',
        'group__name',
        'group__abbreviation',
        'group__officer_email',
        'group__athena_locker',
    ]
admin.site.register(groups.models.GroupNote, Admin_GroupNote)


class OfficerRoleAdmin(VersionAdmin):
    list_display = (
        'id',
        'display_name',
        'slug',
        'max_count',
        'require_student',
        'publicly_visible',
        'grant_user',
    )
    list_display_links = ('id', 'display_name', 'slug', )
    prepopulated_fields = {"slug": ("display_name",)}
admin.site.register(groups.models.OfficerRole, OfficerRoleAdmin)


class OfficeHolderAdmin(VersionAdmin):
    class OfficeHolderPeriodFilter(util.admin.TimePeriodFilter):
        start_field = 'start_time'
        end_field = 'end_time'

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
    list_filter = [
        'role',
        OfficeHolderPeriodFilter,
    ]
admin.site.register(groups.models.OfficeHolder, OfficeHolderAdmin)


class ActivityCategoryAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
    )
    list_display_links = ('id', 'name', )
admin.site.register(groups.models.ActivityCategory, ActivityCategoryAdmin)


class Admin_GroupClass(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'slug',
        'gets_publicity',
    )
    list_display_links = ('id', 'name', 'slug', )
    list_filter = [ 'gets_publicity', ]
    prepopulated_fields = {'slug': ('name', )}
admin.site.register(groups.models.GroupClass, Admin_GroupClass)


class Admin_GroupStatus(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'slug',
        'is_active',
    )
    list_display_links = ('id', 'name', 'slug', )
    list_filter = [ 'is_active', ]
    prepopulated_fields = {'slug': ('name', )}
admin.site.register(groups.models.GroupStatus, Admin_GroupStatus)


class Admin_GroupFunding(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'slug',
        'contact_email',
        'funding_list',
    )
    list_display_links = ('id', 'name', 'slug', )
    prepopulated_fields = {'slug': ('name', )}
admin.site.register(groups.models.GroupFunding, Admin_GroupFunding)


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
admin.site.register(groups.models.AthenaMoiraAccount, Admin_AthenaMoiraAccount)
