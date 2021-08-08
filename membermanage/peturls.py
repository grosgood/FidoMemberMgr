from django.conf.urls import *
from fidoonline.membermanage import petviews

urlpatterns = patterns('fidoonline.membermanage.petviews',
                       (r'^directory/', 'listpets'),
                       (r'^taglist/',   'listtags'),
                       (r'^detail/(?P<pet_id>\d+)', 'detailonepet'),
                       (r'^$', 'listpets'),
                      )
