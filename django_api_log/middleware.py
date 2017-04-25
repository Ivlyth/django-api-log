# -*- coding:utf8 -*-
"""
Author : Myth
Date   : 16/11/24
Email  : belongmyth at 163.com
"""

import json
import logging
import traceback

from datetime import datetime
from django.urls import resolve, Resolver404

from .models import ApiLog
from .settings import settings

logging.basicConfig()
logger = logging.getLogger(u'django-request')

UTF_8 = str('utf-8')


def retrieve_headers(META):
    headers = {}
    for key, value in META.items():
        if not isinstance(value, basestring):
            continue
        if key in (u'CONTENT_LENGTH', u'CONTENT_TYPE', u'REMOTE_ADDR'):
            headers[key] = value
            continue
        if not key.startswith(u'HTTP_'):
            continue
        headers[key[5:]] = value
    return headers


def utf8(content):
    if not content:
        return content
    return content  # .decode(UTF_8)


def get_client_ip(request):
    if 'HTTP_X_FORWARDED_FOR' in request.META:
        return request.META['HTTP_X_FORWARDED_FOR'].split(",")[0].strip()
    elif 'HTTP_X_REAL_IP' in request.META:
        return request.META['HTTP_X_REAL_IP']
    elif 'REMOTE_ADDR' in request.META:
        return request.META['REMOTE_ADDR']
    else:
        return 'ip-not-found'


class ApiLogMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response
        self.exception = None

    def __call__(self, request):
        # start to timing response
        apilog = ApiLog()
        apilog.start_time = datetime.now()
        response = self.get_response(request)

        no_log = getattr(request, u'__NO_LOG__', False)
        no_method_log = getattr(request, u'__NO_%s_LOG__' % request.method, False)

        # 即使标记了忽略log的API, 如果http code >= 400 依然强制不忽略
        if (no_log or no_method_log) and response.status_code < 400:
            return response

        # 默认忽略所有正确的 GET 请求记录
        if request.method == u'GET' and response.status_code < 400 and settings.IGNORE_RIGHT_GET:
            return response

        try:
            apilog.client_ip = get_client_ip(request)
            apilog.method = request.method
            apilog.path = request.path
            apilog.raw_query = json.dumps(request.GET)
            try:
                apilog.raw_request_headers = json.dumps({u'headers': json.dumps(retrieve_headers(request.META))})
            except Exception as e:
                apilog.raw_request_headers = json.dumps({u'headers': u'get request headers failed: %s' % e})
            apilog.raw_request_body = json.dumps({u'body': utf8(request.body)})

            apilog.http_code = response.status_code
            apilog.http_reason = response.reason_phrase
            try:
                apilog.raw_response_headers = json.dumps(
                    {u'headers': json.dumps(dict([v for v in response._headers.values()]))})
            except Exception as e:
                apilog.raw_response_headers = json.dumps({u'headers': u'get response headers failed: %s' % e})

            try:
                r = resolve(request.path)
                apilog.app_name = r.app_name
                apilog.url_name = r.url_name
                apilog.view_name = r.view_name
                apilog.func_name = r.func.func_name
            except Resolver404:
                apilog.app_name = u'__not_resolve__'
                apilog.url_name = u'__not_resolve__'
                apilog.view_name = u'__not_resolve__'
                apilog.func_name = u'__not_resolve__'

            # only record http response body when response http code >= 400
            if response.status_code >= 400 or request.method != u'GET':
                apilog.raw_response_body = json.dumps({u'body': utf8(response.content)})

            # for uncaught_exception
            uncaught_exception = getattr(request, 'uncaught_exception', None)
            if uncaught_exception:
                apilog.exception = str(uncaught_exception)
                apilog.traceback = getattr(request, 'uncaught_exception_format', '')

            apilog.end_time = datetime.now()
            apilog.duration = round((apilog.end_time - apilog.start_time).total_seconds() * 1000, 2)
            apilog.save()
            try:
                if response.status_code >= 400:
                    notify_func = settings.NOTIFY_FUNC
                    if callable(notify_func):
                        notify_func(apilog.json(request))
            except Exception:
                logger.exception(u'Error when notify api error:')
        except Exception:
            logger.exception(u'Error when save api log:')

        return response

    def process_exception(self, request, exception):
        request.uncaught_exception = exception
        request.uncaught_exception_format = traceback.format_exc()
