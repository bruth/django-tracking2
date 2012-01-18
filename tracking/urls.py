from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('tracking.views',
    url(r'^dashboard/$', 'stats', name='tracking-dashboard'),
)
