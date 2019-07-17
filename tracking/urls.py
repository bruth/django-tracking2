from django.conf.urls import url

from tracking.views import (
    dashboard,
    visitor_overview,
    visitor_visits,
    visitor_page_detail,
    visitor_pageview_detail,
    page_overview,
    page_detail,
)

urlpatterns = [
    url(r'^$', dashboard, name='tracking-dashboard'),
    url(r'^visitors/(?P<user_id>.*)/page/$', visitor_page_detail, name='tracking-visitor-page-detail'),
    url(r'^visitors/(?P<user_id>.*)/pageview/(?P<pageview_id>.*)/$', visitor_pageview_detail, name='tracking-pageview-detail'),
    url(r'^visitors/(?P<user_id>.*)/$', visitor_overview, name='tracking-visitor-overview'),
    url(r'^visits/(?P<visit_id>.*)/$', visitor_visits, name='tracking-visitor-visits'),
    url(r'^pages/$', page_overview, name='tracking-page-overview'),
    url(r'^page/$', page_detail, name='tracking-page-detail'),
]
