from django.conf.urls import url

from tracking.views import (
    dashboard,
    visitor_overview,
    visitor_visits,
)

urlpatterns = [
    url(r'^$', dashboard, name='tracking-dashboard'),
    url(r'^visitors/(?P<user_id>.*)/$', visitor_overview, name='tracking-visitor-overview'),
    url(r'^visits/(?P<visit_id>.*)/$', visitor_visits, name='tracking-visitor-visits'),
]
