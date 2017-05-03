from setuptools import setup

setup(
    name='django_api_log',
    version='0.2.3',
    packages=['django_api_log', 'django_api_log.migrations'],
    url='https://github.com/MythRen/django-api-log',
    license='BSD',
    author='Myth',
    author_email='belongmyth@163.com',
    description='Django reusable app for record request/response information to database for alert and audit.'
)
