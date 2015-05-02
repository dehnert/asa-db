from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib.auth.views import login, logout
from django.views.generic.base import RedirectView, TemplateView

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

import groups.urls
import forms.views
import space.views

about_patterns = patterns('',
    url(
        r'^data/$',
        RedirectView.as_view(url='http://web.mit.edu/asa/database/use-of-data.html', permanent=True, ),
        name='about-data',
    ),
    url(
        r'^roles/$',
        'groups.views.view_roles_descriptions',
        name='about-roles',
    ),
    url(
        r'^$',
        TemplateView.as_view(template_name='about/index.html'),
        {'pagename':'about'}, name='about',
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

    # Membership confirmations
    url(
        regex=r'^membership/update/$',
        view=forms.views.group_membership_update_select_group,
        name='membership-update-cycle',
    ),
    url(r'^membership/update/(?P<cycle_slug>[\w-]+)/(?P<pk>\d+)/$', forms.views.group_membership_update, name='membership-update-group', ),
    url(r'^membership/confirm/$', forms.views.person_membership_update, name='membership-confirm', ),
    url(
        r'^membership/thanks/$',
        TemplateView.as_view(template_name='membership/thanks.html'), { 'pagename':'groups' },
        name='membership-thanks',
    ),
    url(r'^membership/submitted/$', forms.views.View_GroupMembershipList.as_view(), name='membership-submitted', ),
    url(r'^membership/admin/$', forms.views.View_GroupConfirmationCyclesList.as_view(), name='membership-admin', ),
    url(r'^membership/admin/issues/(?P<slug>[\w-]+).csv$', forms.views.group_confirmation_issues, name='membership-issues', ),
    url(r'^membership/people-lookup/((?P<pk>\d+)/)?$', forms.views.people_status_lookup, name='membership-people-lookup', ),

    # Midway
    url(r'^midway/$', forms.views.View_Midways.as_view(), name='midway-list', ),
    url(r'^midway/latest/$', forms.views.midway_map_latest, name='midway-map-latest', ),
    url(r'^midway/(?P<slug>[\w-]+)/$', forms.views.MidwayMapView.as_view(), name='midway-map', ),
    url(r'^midway/(?P<slug>[\w-]+)/assign/$', forms.views.midway_assignment_upload, name='midway-assign', ),

    # Group list
    (r'^groups/', include(groups.urls.urls(), ), ),

    # Space
    url(r'^space/dump/locker-access.csv$', space.views.dump_locker_access, name='space-dump-locker-access', ),
    url(r'^space/dump/office-access.csv$', space.views.dump_office_access, name='space-dump-office-access', ),
    url(r'^space/$', space.views.summary, name='space-summary', ),
    url(r'^space/lock_types.html$', space.views.lock_types, name='space-lock-type', ),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
    url(r'^accounts/login/password/', 'django.contrib.auth.views.login', name='login-password', ),
    url(r'^accounts/login/',  'mit.scripts_login',  name='login', ),
    url(r'^accounts/logout/', logout, name='logout', ),
)

# Static and media file serving in DEBUG
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += staticfiles_urlpatterns()
