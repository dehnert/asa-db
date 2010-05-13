import forms.models
from django.contrib import admin

class FYSMAdmin(admin.ModelAdmin):
    list_display = (
        'group',
        'year',
        'website',
        'contact_email',
    )
    list_display_links = ('group', 'year', )

class FYSMTagsAdmin(admin.ModelAdmin):
    list_display = (
        'name',
    )

admin.site.register(forms.models.FYSM, FYSMAdmin)
admin.site.register(forms.models.FYSMTags, FYSMTagsAdmin)
