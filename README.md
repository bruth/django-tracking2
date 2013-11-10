Overview
========

[![Bitdeli Badge](https://d2weczhvl823v0.cloudfront.net/bruth/django-tracking2/trend.png)](https://bitdeli.com/free "Bitdeli Badge")

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
* [South][2] (if you want to use the packaged migrations)

[1]: https://docs.djangoproject.com/en/1.3/topics/http/sessions/
[2]: http://pypi.python.org/pypi/South

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

Settings
--------
`TRACK_AJAX_REQUESTS` - If True, AJAX requests will be tracked. Default
is False

`TRACK_ANONYMOUS_USERS` - If False, anonymous users will not be tracked.
Default is True

`TRACK_PAGEVIEWS` - If True, individual pageviews will be tracked.

`TRACK_IGNORE_URLS` - A list of regular expressions that will be matched
against the `request.path_info` (`request.path` is stored, but not matched
against). If they are matched, the pageview record will not be saved. Default
includes 'favicon.ico' and 'robots.txt'. Note, static and media are not included
since they should be served up statically Django's static serve view or via
a lightweight server in production. Read more
[here](https://docs.djangoproject.com/en/dev/howto/static-files/#serving-other-directories)

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
* `/dashboard/` - overview of all visitor activity

Templates
---------
* `tracking/dashboard.html` - for the dashboard page
* `tracking/snippets/stats.html` - standalone content for the dashboard page
  (simplifies overriding templates)
