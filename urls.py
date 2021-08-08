
import os
from django.conf.urls import *
from django.contrib import admin
import fidoonline.settings as settings

admin.autodiscover()
# 2020-Dec-21 - can't do statistics
urlpatterns = patterns('',
    (r'^accounts/profile/$', 'django.contrib.auth.views.login', {'template_name': 'membermanage/login.html'}),
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),
    (r'^login/', 'django.contrib.auth.views.login', {'template_name': 'membermanage/login.html'} ),
    (r'^member/', include('fidoonline.membermanage.urls')),
    (r'^pet/', include('fidoonline.membermanage.peturls')),
    (r'^sitemedia/(?P<path>.*)$', 'django.views.static.serve', {'document_root': os.path.join(settings.PROJECT_PATH, 'media')}),
#   (r'^statistics/', include('fidoonline.membermanage.statisticsurls')),
    (r'^$', 'fidoonline.membermanage.starthereview.start'),                   
)
