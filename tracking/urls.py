from django.conf.urls import patterns, url
from tracking.views import UserVisits

urlpatterns = patterns('tracking.views',
    url(r'^dashboard/$', 'stats', name='tracking-dashboard'),
    url(r'^user/(\d+)/$', 'user_detail', name='tracking-user-detail'),
    url(r'^user-visits/(\d+)/$', UserVisits.as_view(), name='tracking-user-visits'),
)
