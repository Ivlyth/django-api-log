Django API Log
==============

Django reusable app for record request/response information to database for alert and audit.


### Installation
`pip install django-api-log`

### Usage.

1. add `django_api_log.apps.DjangoApiLogConfig` to INSTALLED_APPS.
2. add `django_api_log.middleware.ApiLogMiddleware` to MIDDLEWARE (MIDDLEWARE_CLASSES if you use django<1.10)
3. run `python manage.py migrate`
4. config urlpatterns
   eg: add `url(r'^api-log', include(u'django_api_log.urls'), name='django_api_log')` to your root urlpatterns
   or other urlpatterns you like .
   
then, everything should be fine. :)

### Query saved logs
open your browser then visit YOUR_API_HOST/api-log (or use the path you use)