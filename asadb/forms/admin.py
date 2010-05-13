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


admin.site.register(forms.models.FYSM, FYSMAdmin)
