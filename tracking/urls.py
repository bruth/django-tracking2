from django.conf.urls import patterns, url

urlpatterns = patterns('tracking.views',
    url(r'^dashboard/$', 'stats', name='tracking-dashboard'),
    url(r'^user/(\d+)/$', 'user_detail', name='tracking-user-detail'),
)
