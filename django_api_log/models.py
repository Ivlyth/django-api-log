# -*- coding:utf8 -*-
"""
Author : Myth
Date   : 16/11/24
Email  : belongmyth at 163.com
"""

from __future__ import unicode_literals

import json

from datetime import datetime
from django.db import models
from django.urls import reverse
from .apps import DjangoApiLogConfig


# Create your models here.

class JSONModel(models.Model):
    class Meta:
        abstract = True

    def json(self):
        fields = self._meta.fields

        data = {}
        include_properties = getattr(self, 'INCLUDE_PROPERTIES', [])
        for proper in include_properties:
            data[proper] = getattr(self, proper, None)

        ignore_fields = getattr(self, 'IGNORE_FIELDS', None)
        for field in fields:
            field_name = field.attname
            if ignore_fields and field_name in ignore_fields:
                continue
            field_value = getattr(self, field_name, None)
            if isinstance(field_value, datetime):
                field_value = field_value.strftime('%Y-%m-%d %H:%M:%S.%f')
            data[field_name] = field_value
        return data


class BaseModel(JSONModel):
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']
        abstract = True


class ApiLog(BaseModel):
    client_ip = models.CharField(max_length=20)  # client ip address
    method = models.CharField(max_length=10)  # request method
    path = models.CharField(max_length=200)  # request path
    raw_query = models.TextField()  # request query
    raw_request_headers = models.TextField()  # request headers
    raw_request_body = models.TextField()  # request body
    http_code = models.IntegerField()  # response http code
    http_reason = models.CharField(max_length=100)  # response http reason
    raw_response_headers = models.TextField()  # response headers
    raw_response_body = models.TextField()  # response body
    app_name = models.CharField(max_length=100, default='')  # app name
    url_name = models.CharField(max_length=100, default='')  # url name
    view_name = models.CharField(max_length=100, default='')  # view name(app_name:url_name)
    func_name = models.CharField(max_length=100, default='')  # function name
    exception = models.TextField(max_length=100)  # exception name
    traceback = models.TextField()  # traceback, if any
    django_error_page = models.TextField(null=True, blank=True)  # django error page, if http_code == 500
    start_time = models.DateTimeField(auto_now=True)  # request start
    end_time = models.DateTimeField(auto_now_add=True)  # when return response
    duration = models.FloatField()  # last for how long in million seconds

    def __repr__(self):
        return 'Django API Log: %s %s -> %s' % (self.method, self.path, self.http_code)

    def __str__(self):
        return self.__repr__()

    IGNORE_FIELDS = (
        'raw_query', 'raw_request_headers', 'raw_request_body', 'raw_response_headers', 'raw_response_body', 'django_error_page')

    INCLUDE_PROPERTIES = ('query', 'request_headers', 'request_body', 'response_headers', 'response_body')

    def json(self, request):
        data = super(ApiLog, self).json()
        # request uesd to build full url on the fly
        data['data_url'] = request.build_absolute_uri(
            reverse('%s:%s' % (DjangoApiLogConfig.name, 'view_api_data'), args=(self.id,)))
        data['response_url'] = request.build_absolute_uri(
            reverse('%s:%s' % (DjangoApiLogConfig.name, 'view_api_response'), args=(self.id,)))
        data['django_error_page_url'] = u'%s?format=django' % request.build_absolute_uri(
            reverse('%s:%s' % (DjangoApiLogConfig.name, 'view_api_response'), args=(self.id,)))
        return data

    @property
    def query(self):
        if self.raw_query:
            try:
                return json.loads(self.raw_query)
            except ValueError:
                return self.raw_query
        return None

    @property
    def request_headers(self):
        if self.raw_request_headers:
            try:
                raw_headers = json.loads(self.raw_request_headers)['headers']
                try:
                    return json.loads(raw_headers)
                except ValueError:
                    return raw_headers
            except ValueError:
                return self.raw_response_headers
        return None

    @property
    def request_body(self):
        if self.raw_request_body:
            try:
                raw_body = json.loads(self.raw_request_body)['body']
                try:
                    return json.loads(raw_body)
                except ValueError:
                    return raw_body
            except ValueError:
                return self.raw_request_body
        return None

    @property
    def response_headers(self):
        if self.raw_response_headers:
            try:
                raw_headers = json.loads(self.raw_response_headers)['headers']
                try:
                    return json.loads(raw_headers)
                except ValueError:
                    return raw_headers
            except ValueError:
                return self.raw_response_headers
        return None

    @property
    def response_body(self):
        if self.raw_response_body:
            try:
                raw_body = json.loads(self.raw_response_body)['body']
                try:
                    return json.loads(raw_body)
                except ValueError:
                    return raw_body
            except ValueError:
                return self.raw_response_body
        return None
