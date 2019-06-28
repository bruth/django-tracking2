from django.conf.urls import url

from tracking.views import (
    dashboard,
    visitor_overview,
)

urlpatterns = [
    url(r'^$', dashboard, name='tracking-dashboard'),
    url(r'^visitors/(?P<user_id>.*)/$', visitor_overview, name='tracking-visitor-overview'),
]
