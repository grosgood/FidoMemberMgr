from django.conf.urls import *
from fidoonline.membermanage import statistics

urlpatterns = patterns('fidoonline.membermanage.statistics',
                       (r'^directory/', 'summary'),
                       (r'^$', 'summary'),
                      )
