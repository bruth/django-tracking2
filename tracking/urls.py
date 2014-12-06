from django.conf.urls import patterns, url

urlpatterns = patterns(
    'tracking.views',
    url(r'^$', 'dashboard', name='tracking-dashboard'),
)
