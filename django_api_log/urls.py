# -*- coding:utf8 -*-
"""
Author : Myth
Date   : 16/11/24
Email  : belongmyth at 163.com
"""

from django.conf.urls import url
from .apps import DjangoApiLogConfig
from .views import query_api_log, view_api_response, view_api_data

app_name = DjangoApiLogConfig.name

urlpatterns = [
    url(r'^$', query_api_log, name='query_api_log'),
    url(r'^(?P<log_id>\d+)$', view_api_data, name='view_api_data'),
    url(r'^(?P<log_id>\d+)/response$', view_api_response, name='view_api_response'),
]
