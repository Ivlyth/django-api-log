# -*- coding:utf8 -*-
"""
Author : Myth
Date   : 16/11/24
Email  : belongmyth at 163.com
"""

from datetime import datetime
from django.http import JsonResponse, HttpResponse

from .models import ApiLog

NOT_SET = u'__NOT_SET__'

DATETIME_FORMAT = u'%Y-%m-%d %H:%M:%S'


def BadRequestResponse(reason):  # Bad RequestResponse
    return JsonResponse({'detail': reason}, status=400)


# Create your views here.
def query_api_log(request):
    '''
    query api log by filter support
    :param request: current request instance, used in ApiLog.json() to build absolute uri.
    :return:
    '''

    request.__NO_LOG__ = True

    query_data = request.GET

    # query log for log.start_time >= start_time
    start_time = query_data.get('start_time', None)
    # query log for log.end_time <= end_time
    end_time = query_data.get('end_time', None)

    if start_time:
        try:
            q_start_time = datetime.strptime(start_time, DATETIME_FORMAT)
        except ValueError:
            return BadRequestResponse(u'invalid format of start_time: %s, should be %s' % (start_time, DATETIME_FORMAT))
    else:
        q_start_time = None

    if end_time:
        try:
            q_end_time = datetime.strptime(start_time, DATETIME_FORMAT)
        except ValueError:
            return BadRequestResponse(u'invalid format of end_time: %s, should be %s' % (end_time, DATETIME_FORMAT))
    else:
        q_end_time = None

    # pagination, current page number
    page = query_data.get(u'page', 1)
    try:
        q_page = int(page)
        q_page = max(q_page, 1)  # page can not less than 1
    except ValueError:
        return BadRequestResponse(u'invalid page number: %s, should be a integer value' % page)

    # how many items per page, default is 20
    page_size = query_data.get(u'page_size', 20)
    try:
        q_page_size = int(page_size)
        q_page_size = min(q_page_size, 50)  # max page size up to 50.
    except ValueError:
        return BadRequestResponse(u'invalid page size: %s, should be a integer value' % page_size)

    # all ApiLog field names
    field_names = [f.attname for f in ApiLog._meta.fields]

    # order by which field and in which direction
    # default is order by created desc(set in model's Meta)
    order_by = query_data.get(u'order_by', None)
    if order_by:
        if order_by[0] in u'+-':
            if order_by[1:] not in field_names:
                return BadRequestResponse(
                    u'invalid order by field: %s, should be one of: %s' % (order_by[1:], u','.join(field_names)))
            q_order_by = order_by
        else:
            if order_by not in field_names:
                return BadRequestResponse(
                    u'invalid order by field: %s, should be one of: %s' % (order_by, u','.join(field_names)))
            q_order_by = order_by
    else:
        q_order_by = None

    # query by django app name
    q_app_name = query_data.get(u'app_name', None)
    # query by view function name
    q_func_name = query_data.get(u'func_name', None)
    # query by view name (in format: app_name:function_name)
    q_view_name = query_data.get(u'view_name', None)
    # query by url_name, if you provide in your url_patterns
    q_url_name = query_data.get(u'url_name', None)

    # query by duration range
    duration_start = query_data.get(u'duration_start', NOT_SET)
    duration_end = query_data.get(u'duration_end', NOT_SET)
    if duration_start is not NOT_SET:
        try:
            q_duration_start = float(duration_start)
        except ValueError:
            return BadRequestResponse(u'invalid duration start: %s, should be a float value' % duration_start)
    else:
        q_duration_start = None

    if duration_end is not NOT_SET:
        try:
            q_duration_end = float(duration_end)
        except ValueError:
            return BadRequestResponse(u'invalid duration end: %s, should be a float value' % duration_start)
    else:
        q_duration_end = None

    # response http code
    q_http_code = query_data.get(u'http_code', None)

    # request path
    q_request_path = query_data.get(u'request_path', None)

    # control which filed return to the client
    show_fields = query_data.get(u'show', '').split(',')
    q_show_fields = []

    if show_fields:
        for field in show_fields:
            if field in field_names:
                q_show_fields.append(field)

    queryset = ApiLog.objects
    # start time
    if q_start_time:
        queryset = queryset.filter(start_time__gte=q_start_time)
    if q_end_time:
        queryset = queryset.filter(end_time__lte=q_end_time)
    if q_duration_start:
        queryset = queryset.filter(duration__gte=q_duration_start)
    if q_duration_end:
        queryset = queryset.filter(duration__lte=q_duration_end)
    if q_app_name:
        queryset = queryset.filter(app_name=q_app_name)
    if q_view_name:
        queryset = queryset.filter(view_name=q_view_name)
    if q_func_name:
        queryset = queryset.filter(func_name=q_func_name)
    if q_url_name:
        queryset = queryset.filter(url_name=q_url_name)
    if q_http_code:
        queryset = queryset.filter(http_code=q_http_code)
    if q_request_path:
        queryset = queryset.filter(path=q_request_path)
    if q_order_by:
        queryset = queryset.order_by(q_order_by)

    offset = (q_page - 1) * q_page_size
    total = queryset.count()
    logs = queryset.all()[offset: offset + q_page_size]

    results = []
    for log in logs:
        if q_show_fields:
            log_json = {}
            for field_name in q_show_fields:
                field_value = getattr(log, field_name)
                if isinstance(field_value, datetime):
                    field_value = field_value.strftime(u'%Y-%m-%d %H:%M:%S.%f')
                log_json[field_name] = field_value
            results.append(log_json)
        else:
            results.append(log.json(request))
    return JsonResponse({
        u'page': q_page,
        u'page_size': q_page_size,
        u'total': total,
        u'logs': results
    })


def view_api_data(request, log_id):
    '''
    view full data for special log
    :param request: current request instance
    :param log_id: special log id
    :return:
    '''
    request.__NO_LOG__ = True
    log = ApiLog.objects.filter(pk=log_id).first()
    if not log:
        return JsonResponse({u'detail': u'log id does not exist'})
    return JsonResponse(log.json(request))


def view_api_response(request, log_id):
    '''
    only view response for special log
    useful for 500 error page
    :param request: current request instance
    :param log_id: special log id
    :return:
    '''
    request.__NO_LOG__ = True
    log = ApiLog.objects.filter(pk=log_id).first()
    if not log:
        return JsonResponse({u'detail': u'log id does not exist'})

    from_ = request.GET.get('from', '')
    if from_ == 'django':
        response_body = log.django_error_page if log.django_error_page else log.response_body
    else:
        response_body = log.response_body
    if not response_body:
        return JsonResponse({u'detail': u'<log response body is empty>'})
    if isinstance(response_body, (dict, list)):
        return JsonResponse({
            u'response_body': response_body
        })
    return HttpResponse(response_body)