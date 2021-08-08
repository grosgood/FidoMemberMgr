from django.conf.urls import *
from fidoonline.membermanage import views

urlpatterns = patterns('fidoonline.membermanage.views',
                       (r'^directory/', 'memberlist'),
                       (r'^detailold/new', 'createonemember'),
                       (r'^detailold/(?P<member_id>\d+)', 'detailonemember'),
                       (r'^$', 'memberlist')
                      )
urlpatterns += patterns('fidoonline.membermanage.memberviews',
                        (r'^detail/(?P<member_id>\d+)',                           'detailmemberframeset'),
                        (r'^detail/contact/(?P<member_id>\d+)',                   'detailmembercontact'),
                        (r'^detail/dues/(?P<member_id>\d+)',                      'detailmemberdues'),
                        (r'^detail/pets/(?P<member_id>\d+)',                      'detailmemberpets'),
                        (r'^detail/journal/(?P<member_id>\d+)',                   'detailmemberjournal'),
                        (r'^detail/preferences/(?P<member_id>\d+)',               'detailmemberpreferences'),
                        (r'^detail/findmember/(?P<bannerflag>True|False)',        'findmemberbyname'), 
                       )

urlpatterns += patterns('fidoonline.membermanage.memberactions',
                        (r'^detail/changename/(?P<member_id>\d+)',                'requestchangename'),
                        (r'^detail/changeaddress/(?P<member_id>\d+)',             'requestchangeaddress'),
                        (r'^detail/changeemail/(?P<member_id>\d+)',               'requestchangeemail'),
                        (r'^detail/changephone/(?P<member_id>\d+)',               'requestchangephone'),
                        (r'^detail/addpayment/(?P<member_id>\d+)',                'recordduespayment'),
                        (r'^detail/addpet/(?P<member_id>\d+)',                    'recordpet'),
                        (r'^detail/changepet/(?P<member_id>\d+)/(?P<pet_id>\d+)', 'changepet'),
                        (r'^detail/addjournalentry/(?P<member_id>\d+)',           'addjournalrecord'),
                        (r'^detail/setmemberpreference/(?P<member_id>\d+)',       'setmemberpreferences')
                       )

urlpatterns += patterns('fidoonline.membermanage.membercreate',
                        (r'^detail/new/name',                                     'makenewrecord'),
                        (r'^detail/new/address/(?P<member_id>\d+)',               'addaddress'),
                        (r'^detail/new/email/(?P<member_id>\d+)',                 'addemail'),
                        (r'^detail/new/phone/(?P<member_id>\d+)',                 'addphone'),
                        (r'^detail/new/payment/(?P<member_id>\d+)',               'addduespayment'),
                        (r'^detail/new/addpet/(?P<member_id>\d+)',                'addpet'),
                        (r'^detail/new/copymodifymember/(?P<member_id>\d+)',      'copymodifymember'),
                        (r'^detail/new/setmemberpreference/(?P<member_id>\d+)',   'addpreference')
                       )
