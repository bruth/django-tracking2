from django.conf.urls import patterns, url
from tracking.views import UserVisits, PageViews
from django.contrib.auth.decorators import permission_required

urlpatterns = patterns('tracking.views',
    url(r'^dashboard/$', 'stats', name='tracking-dashboard'),
    url(r'^user/(\d+)/$', 'user_detail', name='tracking-user-detail'),
    url(r'^user-visits/(\d+)/$', (permission_required('tracking.view_visitor')
                                  (UserVisits.as_view())),
        name='tracking-user-visits'),
    url(r'^page-views/(\w+)/$', (permission_required('tracking.view_visitor')
                                  (PageViews.as_view())),
        name='tracking-pageviews'),
)
