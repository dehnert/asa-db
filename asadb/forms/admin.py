from django.contrib import admin

import forms.models

class FYSMAdmin(admin.ModelAdmin):
    list_display = (
        'group',
        'display_name',
        'year',
        'website',
        'contact_email',
    )
    list_display_links = ('group', 'display_name', 'year', )
    list_filter = ('year', 'categories', )
    search_fields = ('group__name', 'group__abbreviation', 'display_name', 'year', )

class FYSMCategoryAdmin(admin.ModelAdmin):
    list_display = (
        'name',
    )
    prepopulated_fields = {"slug": ("name",)}

admin.site.register(forms.models.FYSM, FYSMAdmin)
admin.site.register(forms.models.FYSMCategory, FYSMCategoryAdmin)

class Admin_GroupConfirmationCycle(admin.ModelAdmin):
    list_display = (
        'pk',
        'name',
        'slug',
        'create_date',
    )
    list_display_links = ('pk', 'name', 'slug', )
    prepopulated_fields = {"slug": ("name",)}
admin.site.register(forms.models.GroupConfirmationCycle, Admin_GroupConfirmationCycle)

class Admin_GroupMembershipUpdate(admin.ModelAdmin):
    list_display = (
        'pk',
        'group',
        'cycle',
        'update_time',
        'updater_name',
        'updater_title',
        'num_undergrads',
        'num_grads',
        'num_alum',
        'num_other_affiliate',
        'num_other',
    )
    list_filter = ('cycle', )
    list_display_links = ('pk', 'group', )
    search_fields = ('group__name', 'group__abbreviation', 'updater_name', )
admin.site.register(forms.models.GroupMembershipUpdate, Admin_GroupMembershipUpdate)

class Admin_PersonMembershipUpdate(admin.ModelAdmin):
    list_display = (
        'pk',
        'username',
        'cycle',
        'update_time',
        'deleted',
        'valid',
    )
    list_filter = ('valid', 'cycle', 'groups', )
    list_display_links = ('pk', 'username', 'cycle', )
    search_fields = ('username', 'groups__officer_email', 'groups__name', 'groups__abbreviation', )
admin.site.register(forms.models.PersonMembershipUpdate, Admin_PersonMembershipUpdate)

class Admin_Midway(admin.ModelAdmin):
    list_display = (
        'pk',
        'name',
        'slug',
        'date',
    )
    list_display_links = list_display
    search_fields = ('name', )
    prepopulated_fields = {"slug": ("name",)}
admin.site.register(forms.models.Midway, Admin_Midway)

class Admin_MidwayAssignment(admin.ModelAdmin):
    list_display = (
        'pk',
        'midway',
        'location',
        'group',
    )
    list_display_links = list_display
    list_filter = ('midway', )
    search_fields = ('location', 'group__name', )
admin.site.register(forms.models.MidwayAssignment, Admin_MidwayAssignment)
