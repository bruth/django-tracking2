from django.conf.urls import url

from tracking.views import dashboard

urlpatterns = [
    url(r'^$', dashboard, name='tracking-dashboard'),
]
