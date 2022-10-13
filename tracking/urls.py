from django.urls import re_path

from tracking.views import dashboard

urlpatterns = [
    re_path(r'^$', dashboard, name='tracking-dashboard'),
]
