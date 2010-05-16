import forms.models
from django.contrib import admin

class FYSMAdmin(admin.ModelAdmin):
    list_display = (
        'group',
        'display_name',
        'year',
        'website',
        'contact_email',
    )
    list_display_links = ('group', 'display_name', 'year', )

class FYSMCategoryAdmin(admin.ModelAdmin):
    list_display = (
        'name',
    )
    prepopulated_fields = {"slug": ("name",)}

admin.site.register(forms.models.FYSM, FYSMAdmin)
admin.site.register(forms.models.FYSMCategory, FYSMCategoryAdmin)
