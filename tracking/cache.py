# Inspired by http://eflorenzano.com/blog/2008/11/28/drop-dead-simple-django-caching/
from django.db import models
from django.core.cache import cache
from django.db.models.query import QuerySet


def instance_cache_key(instance):
    opts = instance._meta
    if hasattr(opts, 'model_name'):
        name = opts.model_name
    else:
        name = opts.module_name
    return '%s.%s:%s' % (opts.app_label, name, instance.pk)


class CacheQuerySet(QuerySet):
    def filter(self, *args, **kwargs):
        pk = None
        for val in ('pk', 'pk__exact', 'id', 'id__exact'):
            if val in kwargs:
                pk = kwargs[val]
                break
        if pk is not None:
            opts = self.model._meta
            key = '%s.%s:%s' % (opts.app_label, opts.model_name, pk)
            obj = cache.get(key)
            if obj is not None:
                self._result_cache = [obj]
        return super(CacheQuerySet, self).filter(*args, **kwargs)


class CacheManager(models.Manager):
    def get_queryset(self):
        return CacheQuerySet(self.model)

