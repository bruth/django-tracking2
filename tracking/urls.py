from django.conf.urls import url

from tracking.views import (
    dashboard,
    visitor_overview,
    visitor_visits,
    visitor_page_detail,
)

urlpatterns = [
    url(r'^$', dashboard, name='tracking-dashboard'),
    url(r'^visitors/(?P<user_id>.*)/$', visitor_overview, name='tracking-visitor-overview'),
    url(r'^visits/(?P<visit_id>.*)/$', visitor_visits, name='tracking-visitor-visits'),
    url(r'^visitors/(?P<user_id>.*)/page/(?P<page_url>.*)/$', visitor_page_detail, name='tracking-page-detail'),
]
