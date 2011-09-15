from django.conf.urls.defaults import *

import groups.views

group_patterns = patterns('',
    url(r'^$', groups.views.GroupDetailView.as_view(), name='group-detail', ),
    url(r'^edit/main$', groups.views.manage_main, name='group-manage-main', ),
    url(r'^edit/officers$', groups.views.manage_officers, name='group-manage-officers', ),
    url(r'^history/$', groups.views.GroupHistoryView.as_view(), name='group-manage-history', ),
)

groups_patterns = patterns('',
    (r'^(?P<pk>\d+)/', include(group_patterns, ), ),
    url(r'^$', groups.views.GroupListView.as_view(), name='list', ),
    url(r'^search/$', groups.views.search_groups, name='search', ),
    url(r'^recent_changes/$', groups.views.GroupHistoryView.as_view(), name='manage-history', ),
    url(r'^signatories/$', groups.views.view_signatories, name='signatories', ),
)

def urls():
    return (groups_patterns , 'groups', 'groups', )
