from django.conf.urls.defaults import *
from django.contrib.auth.views import login, logout
from django.views.generic import list_detail

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

import settings

import groups.urls
import forms.views
import space.views

about_patterns = patterns('',
    url(
        r'^data/$',
        'django.views.generic.simple.redirect_to',
        {'url': 'http://web.mit.edu/asa/database/use-of-data.html'},
        name='about-data',
    ),
    url(
        r'^$',
        'django.views.generic.simple.direct_to_template',
        {'template': 'about/index.html', 'extra_context': { 'pagename':'about' }, },
        name='about',
    ),
)

urlpatterns = patterns('',
    # Example:
    # (r'^asadb/', include('asadb.foo.urls')),
    url(r'^$', 'groups.views.view_homepage', name='homepage', ),
    (r'^about/', include(about_patterns, ), ),

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

    url(
        regex=r'^membership/update/$',
        view=forms.views.group_membership_update_select_group,
        name='membership-update-cycle',
    ),
    url(r'^membership/update/(?P<cycle_slug>[\w-]+)/(?P<pk>\d+)/$', forms.views.group_membership_update, name='membership-update-group', ),
    url(r'^membership/confirm/$', forms.views.person_membership_update, name='membership-confirm', ),
    url(
        r'^membership/thanks/$',
        'django.views.generic.simple.direct_to_template',
        {'template': 'membership/thanks.html', 'extra_context': { 'pagename':'groups' }, },
        name='membership-thanks',
    ),
    url(r'^membership/submitted/$', forms.views.View_GroupMembershipList.as_view(), name='membership-submitted', ),
    url(r'^membership/admin/issues.csv$', forms.views.group_confirmation_issues, name='membership-issues', ),

    # Group list
    (r'^groups/', include(groups.urls.urls(), ), ),

    # Space
    url(r'^space/dump/locker-access.csv$', space.views.dump_locker_access, name='space-dump-locker-access', ),
    url(r'^space/dump/office-access.csv$', space.views.dump_office_access, name='space-dump-office-access', ),

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
