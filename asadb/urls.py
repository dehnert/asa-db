from django.conf.urls.defaults import *
from django.contrib.auth.views import login, logout
from django.views.generic import list_detail

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

import settings

import forms.views
import groups.models
import groups.views


urlpatterns = patterns('',
    # Example:
    # (r'^asadb/', include('asadb.foo.urls')),
    url(r'^$', 'groups.views.view_homepage', name='homepage', ),

    # FYSM
    url(
        r'^fysm/submit/select/$',
        forms.views.select_group_fysm,
        name='fysm-select',
    ),
    url(r'^fysm/submit/manage/(\d+)/$', forms.views.fysm_manage, name='fysm-manage', ),
    url(r'^fysm/submit/thanks/(\d+)/$', forms.views.fysm_thanks, name='fysm-thanks', ),
    url(r'^fysm/(\d+)/view/(\d+)/$', forms.views.fysm_view, name='fysm-view', ),
    url(r'^fysm/(\d+)/(join|website)/(\d+)/$', forms.views.fysm_link, name='fysm-link', ),
    url(r'^fysm/(?:(\d+)/)?(?:([\w-]+)/)?$', forms.views.fysm_by_years, name='fysm', ),

    # Group editing
    url(r'^group/(\d+)/edit/main$', groups.views.manage_main, name='group-manage-main', ),
    url(r'^group/(\d+)/edit/officers$', groups.views.manage_officers, name='group-manage-officers', ),

    # Group list
    url(r'^groups/$', groups.views.GroupListView.as_view(), name='group-list', ),
    url(r'^group/(?P<pk>\d+)/$', groups.views.GroupDetailView.as_view(), name='group-detail', ),
    url(r'^groups/recent_changes/$', groups.views.GroupHistoryView.as_view(), name='groups-manage-history', ),
    url(r'^group/(?P<group>\d+)/history/$', groups.views.GroupHistoryView.as_view(), name='group-manage-history', ),
    url(r'^groups/signatories/$', groups.views.view_signatories, name='groups-signatories', ),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
    url(r'^accounts/login/password/', 'django.contrib.auth.views.login', name='login-password', ),
    url(r'^accounts/login/',  'mit.scripts_login',  name='login', ),
    url(r'^accounts/logout/', logout, name='logout', ),
)

if settings.DEBUG:
    print "In debug mode; enabling static media serving"
    from django.views.static import serve
    _media_url = settings.MEDIA_URL
    if _media_url.startswith('/'):
        _media_url = _media_url[1:]
        urlpatterns += patterns('',
                                (r'^%s(?P<path>.*)$' % _media_url,
                                serve,
                                {'document_root': settings.MEDIA_ROOT}))
    del(_media_url, serve)
