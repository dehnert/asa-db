from django.conf.urls.defaults import *

import groups.views
import space.views

group_patterns = patterns('',
    url(r'^$', groups.views.GroupDetailView.as_view(), name='group-detail', ),
    url(r'^edit/main$', groups.views.manage_main, name='group-manage-main', ),
    url(r'^edit/officers$', groups.views.manage_officers, name='group-manage-officers', ),
    url(r'^history/$', groups.views.GroupHistoryView.as_view(), name='group-manage-history', ),
    url(r'^space/$', space.views.manage_access, name='group-space-access', ),
)

groups_patterns = patterns('',
    (r'^(?P<pk>\d+)/', include(group_patterns, ), ),
    url(r'^$', groups.views.GroupListView.as_view(), name='list', ),
    url(r'^startup/$', groups.views.startup_form, name='startup', ),
    url(r'^startup/review/$', groups.views.GroupStartupListView.as_view(), name='startup-list', ),
    url(r'^startup/review/(?P<pk>\d+)$', groups.views.recognize_normal_group, name='startup-recognize', ),
    url(r'^recognize/nge/$', groups.views.recognize_nge, name='recognize-nge', ),
    url(r'^search/$', groups.views.search_groups, name='search', ),
    url(r'^recent_changes/$', groups.views.GroupHistoryView.as_view(), name='manage-history', ),
    url(r'^signatories/$', groups.views.view_signatories, name='signatories', ),
    url(r'^account_lookup/$', groups.views.account_lookup, name='account-lookup', ),
)

def urls():
    return (groups_patterns , 'groups', 'groups', )
