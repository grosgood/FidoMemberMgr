#! /usr/bin/python
"""
Django settings for Fido_Online project.
"""
import os
# import localkeyring as kr # Access methods to the sensitive strings BUG: GNOME-CETRIC KEYRING
from django.core.urlresolvers import reverse

DEBUG          = True
TEMPLATE_DEBUG = DEBUG
PROJECT_PATH   = os.path.realpath(os.path.dirname(__file__)) 

ADMINS = (
     ('Garry Osgood', 'grosgood@garryosgood.com'),
)
LOGIN_URL      = '/login/'
MANAGERS = ADMINS

DATABASES = {
    'default' : {
        'ENGINE'   : 'django.db.backends.mysql',     # fidoonline uses mysql 
##         'NAME'     :  kr.getDatabaseName('login'),   # name of database
##         'USER'     :  kr.getDatabaseUser('login'),   # user with select and update database credentials
##         'PASSWORD' :  kr.getDatabaseSecret('login'), # Once a hacker can step through this script
        'NAME'     :  'garryosg_fidomembership',                 # name of database
        'USER'     :  'garryosg_fido',                        # user with select and update database credentials
        'PASSWORD' :  'Fido47Friends!',              # Once a hacker can step through this script
                                                     # with a python debugger, we're hosed, but it is a
                                                     # bit tricky to get to that state. Not impossible - but tricky.
        'HOST'     : '',                             # currently restricted to local, no over-the-net, operations
        'PORT'     : ''                              # default to standard MySQL port
   }
}

MANAGERS = ADMINS

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.

TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html

LANGUAGE_CODE = 'en-us'

SITE_ID = 1569157

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.

USE_I18N = False

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale

USE_L10N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"

MEDIA_ROOT = os.path.join(PROJECT_PATH, 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"

MEDIA_URL = '/sitemedia/'

# Deprecated with 1.5 - no more ADMIN_MEDIA_PREFIX
# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
# ADMIN_MEDIA_PREFIX = '/media/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    "/home1/garryosg/.local/lib/python/fidoonline/media",
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

STATIC_URL = '/static/'
#STATIC_URL = '/media/'
#STATIC_ROOT = '/media/FireTwo/FidoMembership/fidoonline/static'
STATIC_ROOT = os.path.join(PROJECT_PATH, 'static')

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'gyx)f+s!jc2d6z99subrd=z)lw*$8()l@3cqur65rq=j0^7seo'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'fidoonline.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_PATH, 'templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'fidoonline.membermanage'
)
