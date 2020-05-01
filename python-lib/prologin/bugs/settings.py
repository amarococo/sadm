# Copyright (c) 2020 Association Prologin <info@prologin.org>
#
# SPDX-Licence-Identifier: GPL-3.0+

from prologin.djangoconf import use_profile_config

cfg = use_profile_config('bugs')

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites.apps.SitesConfig',
    'django.contrib.humanize.apps.HumanizeConfig',
    'prologin.bugs.bugs',
    'markdown_deux',
    'bootstrapform',
    'helpdesk',
    'django_prometheus',
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ]
        },
    },
]

MIDDLEWARE = (
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',
)

AUTHENTICATION_BACKENDS = (
    'prologin.sso.django.SSOUserBackend',
    'django.contrib.auth.backends.ModelBackend',
)

ROOT_URLCONF = 'prologin.bugs.urls'

WSGI_APPLICATION = 'prologin.bugs.wsgi.application'


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

SITE_ID = 1

STATIC_URL = '/static/'
STATIC_ROOT = ''

LOGIN_URL = '/helpdesk/login/'

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)


HELPDESK_DEFAULT_SETTINGS = {
    'use_email_as_submitter': False,
    'email_on_ticket_assign': False,
    'email_on_ticket_change': False,
    'login_view_ticketlist': False,
    'tickets_per_page': 100,
}

HELPDESK_KB_ENABLED = False
HELPDESK_PUBLIC_TICKET_DUE_DATE = None
HELPDESK_PUBLIC_TICKET_PRIORITY = 1
HELPDESK_UPDATE_PUBLIC_DEFAULT = True
HELPDESK_STAFF_ONLY_TICKET_CC = True
HELPDESK_CREATE_TICKET_HIDE_ASSIGNED_TO = True
HELPDESK_ALLOW_NON_STAFF_TICKET_UPDATE = True

EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'
