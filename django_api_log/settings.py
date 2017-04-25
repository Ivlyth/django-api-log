# -*- coding:utf8 -*-
"""
Author : Myth
Date   : 16/12/27
Email  : belongmyth at 163.com
"""

from django.conf import settings as django_settings

DJANGO_API_LOG_CONFIG = getattr(django_settings, u'DJANGO_API_LOG', {})
assert isinstance(DJANGO_API_LOG_CONFIG,
                  dict), u'config for DJANGO_API_LOG in django settings must be a dict(or you may NOT set it)!'


class Settings(object):

    @property
    def NOTIFY_FUNC(self):
        '''
        if notify_func is callable, this middleware will
        automatically call this callable with api json data
        :return: callable object or None
        '''
        return DJANGO_API_LOG_CONFIG.get(u'notify_func', None)

    @property
    def IGNORE_RIGHT_GET(self):
        '''
        ignore request with response status code < 400 and method GET
        default is True
        :return:
        '''
        return DJANGO_API_LOG_CONFIG.get(u'ignore_right_get', True)

settings = Settings()
