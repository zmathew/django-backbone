import os

# Settings for running tests.

DEBUG = True
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(os.path.dirname(__file__), 'backbone_tests.db'),
    }
}

# This is just for backwards compatibility
DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = DATABASES['default']['NAME']

ROOT_URLCONF = 'backbone.tests.urls'

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'backbone',
    'backbone.tests',
)

SECRET_KEY = 'pl@#s<ajk3cM$kdh)*4&dsJ'
