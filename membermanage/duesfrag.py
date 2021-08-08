#log# Automatic Logger file. *** THIS MUST BE THE FIRST LINE ***
#log# DO NOT CHANGE THIS LINE OR THE TWO BELOW -* coding: UTF-8 *-
#log# opts = Struct({'__allownew': True, 'logfile': 'ipython_log.py'})
#log# args = []
#log# It is safe to make manual edits below here.
#log#-----------------------------------------------------------------------
from fidoonline.membermanage.models       import Dues, EMailAddress, Journal, MailAddress, Member, MemberPet, MemberPreference, Pet, TelNumber 
dir(Dues)
dir(Dues.objects)
#?Dues.objects.order_by
everypayment = Dues.objects.all().order_by(memberid, paydate)
everypayment = Dues.objects.all().order_by('memberid', 'paydate')
everypayment.count()
everypayment[0]
everypayment[1]
everypayment[2]
everypayment[2].paydate
everypayment[2].memberid
everypayment[2].memberid.memberid
_ip.magic("logstart ")

_ip.magic("Exit ")
