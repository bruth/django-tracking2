Overview
========

[![Build Status](https://travis-ci.org/bruth/django-tracking2.svg?branch=master)](https://travis-ci.org/bruth/django-tracking2)
[![PyPI](https://img.shields.io/pypi/v/django-tracking2.svg)](https://pypi.python.org/pypi/django-tracking2)

django-tracking2 tracks the length of time visitors and registered users
spend on your site. Although this will work for websites, this is more
applicable to web _applications_ with registered users. This does
not replace (nor intend) to replace client-side analytics which is
great for understanding aggregate flow of page views.

**Note: This is not a new version of [django-tracking]. These apps
have very different approaches and, ultimately, goals of tracking users.
This app is about keeping a history of visitor sessions, rather than the
current state of the visitor.**

[django-tracking]: https://github.com/codekoala/django-tracking

Requirements
============
* Django's [session framework][1] installed

[1]: https://docs.djangoproject.com/en/1.11/topics/http/sessions/

Download
========
```bash
pip install django-tracking2
```

Setup
=====
Add `tracking` to your project's `INSTALLED_APPS` setting:

```python
INSTALLED_APPS = (
    ...
    'tracking',
    ...
)
```

If you use Django 1.8+ `tracking` app should follow the app with your user model

Add `tracking.middleware.VisitorTrackingMiddleware` to your project's
`MIDDLEWARE_CLASSES` before the `SessionMiddleware`:

```python
MIDDLEWARE_CLASSES = (
    ...
    'tracking.middleware.VisitorTrackingMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    ...
)
```

Django 1.7+
------------
Django 1.7 brings changes to the way database migrations are handled. If
you do not use database migrations you should not be worried. If you use
south and have not upgraded to django 1.7, you'll have to upgrade to
south==1.0 and django-tracking2==0.3.3.

Releases of djagno-tracking2 after 0.3.3 will not support south.

Settings
--------
`TRACK_AJAX_REQUESTS` - If True, AJAX requests will be tracked. Default
is False

`TRACK_ANONYMOUS_USERS` - If False, anonymous users will not be tracked.
Default is True

`TRACK_PAGEVIEWS` - If True, individual pageviews will be tracked.

`TRACK_IGNORE_URLS` - A list of regular expressions that will be matched
against the `request.path_info` (`request.path` is stored, but not matched
against). If they are matched, the visitor (and pageview) record will not
be saved. Default includes 'favicon.ico' and 'robots.txt'. Note, static and
media are not included since they should be served up statically Django's
static serve view or via a lightweight server in production. Read more
[here](https://docs.djangoproject.com/en/dev/howto/static-files/#serving-other-directories)

`TRACK_IGNORE_STATUS_CODES` - A list of HttpResponse status codes that will be ignored.
If the HttpResponse object has a `status_code` in this blacklist, the pageview record 
will not be saved. For example,

```python
TRACK_IGNORE_STATUS_CODES = [400, 404, 403, 405, 410, 500]
```

`TRACK_REFERER` - If True, referring site for all pageviews will be tracked.  Default is False

`TRACK_QUERY_STRING` - If True, query string for all pageviews will be tracked.  Default is False

Views
-----
To view aggregate data about all visitors and per-registered user stats,
do the following:

Include `tracking.urls` in your `urls.py`:

```python
urlpatterns = patterns('',
    ...
    url(r'^tracking/', include('tracking.urls')),
    ...
)
```

These urls are protected by a custom Django permission `tracking.view_visitor`.
Thus only superusers and users granted this permission can view these pages.

Available URLs
--------------
* `/` - overview of all visitor activity, includes a time picker for
        filtering.

Templates
---------
* `tracking/dashboard.html` - for the dashboard page
* `tracking/snippets/stats.html` - standalone content for the dashboard page
  (simplifies overriding templates)
