from django.conf.urls.defaults import *
from django.contrib.auth.views import login, logout
from django.views.generic import list_detail

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

import settings

import forms.views

urlpatterns = patterns('',
    # Example:
    # (r'^asadb/', include('asadb.foo.urls')),
    url(
        r'^$',
        'django.views.generic.simple.direct_to_template',
        {'template': 'index.html', 'extra_context': { 'pagename':'homepage' }, },
        name='homepage',
    ),

    # FYSM
    url(
        r'^fysm/submit/select/$',
        forms.views.select_group,
        {
            'url_name_after': 'fysm-manage',
            'pagename': 'fysm',
        },
        name='fysm-select', ),
    url(r'^fysm/submit/manage/(\d+)/$', forms.views.fysm_manage, name='fysm-manage', ),
    url(r'^fysm/submit/thanks/(\d+)/$', forms.views.fysm_thanks, name='fysm-thanks', ),
    url(r'^fysm/(?:(\d+)/)?(?:([\w-]+)/)?$', forms.views.fysm_by_years, name='fysm', ),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
    url(r'^accounts/login/',  login,  name='login', ),
    url(r'^accounts/logout/', logout, name='logout', ),
)

if settings.DEBUG:
    from django.views.static import serve
    _media_url = settings.MEDIA_URL
    if _media_url.startswith('/'):
        _media_url = _media_url[1:]
        urlpatterns += patterns('',
                                (r'^%s(?P<path>.*)$' % _media_url,
                                serve,
                                {'document_root': settings.MEDIA_ROOT}))
    del(_media_url, serve)
