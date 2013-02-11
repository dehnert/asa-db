from django.contrib import admin

from reversion.admin import VersionAdmin

import space.models
import util.admin

class Admin_Space(VersionAdmin):
    list_display = (
        'id',
        'number',
        'asa_owned',
        'merged_acl',
    )
    list_display_links = ( 'id', 'number', )
    search_fields = ('number', )
admin.site.register(space.models.Space, Admin_Space)

class Admin_SpaceAssignment(admin.ModelAdmin):
    class AssignmentPeriodFilter(util.admin.TimePeriodFilter):
        start_field = 'start'
        end_field = 'end'

    list_max_show_all = 500
    list_display = (
        'group',
        'space',
        'locker_num',
        'start',
        'end',
    )
    list_display_links = list_display
    list_filter = (AssignmentPeriodFilter, 'space', )
    search_fields = ( 'group__name', 'group__officer_email', 'space__number', )
admin.site.register(space.models.SpaceAssignment, Admin_SpaceAssignment)

class Admin_SpaceAccessListEntry(admin.ModelAdmin):
    class AccessPeriodFilter(util.admin.TimePeriodFilter):
        start_field = 'start'
        end_field = 'end'

    list_display = (
        'group',
        'space',
        'start',
        'end',
        'name',
    )
    list_display_links = list_display
    list_filter = (AccessPeriodFilter, 'space', )
    search_fields = (
        'group__name', 'group__officer_email',
        'space__number',
        'name',
    )
admin.site.register(space.models.SpaceAccessListEntry, Admin_SpaceAccessListEntry)
