import space.models
from django.contrib import admin
from reversion.admin import VersionAdmin

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
    list_max_show_all = 500
    list_display = (
        'group',
        'space',
        'start',
        'end',
    )
    list_display_links = list_display
    list_filter = ('space', )
    search_fields = ( 'group__name', 'group__officer_email', 'space__number', )
admin.site.register(space.models.SpaceAssignment, Admin_SpaceAssignment)

class Admin_SpaceAccessListEntry(admin.ModelAdmin):
    list_display = (
        'group',
        'space',
        'start',
        'end',
        'name',
    )
    list_display_links = list_display
    search_fields = (
        'group__name', 'group__officer_email',
        'space__number',
        'name',
    )
admin.site.register(space.models.SpaceAccessListEntry, Admin_SpaceAccessListEntry)
