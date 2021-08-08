import sys
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'fidoonline.settings'
sys.path.append('/media/FireTwo/FidoMembership')
from fidoonline.membermanage.models import DogTag, Dues, EMailAddress, Journal, MailAddress, Member, MemberPet, MemberPreference, Pet, TelNumber
