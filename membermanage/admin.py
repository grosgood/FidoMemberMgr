from fidoonline.membermanage.models import Member, MailAddress, EMailAddress, TelNumber, Pet, DogTag, MemberPreference, Dues, Journal
from django.contrib import admin

class PrefsInline(admin.TabularInline) :
    model         = MemberPreference
#   fieldsets     = [('Dues paid', {'fields': ('paydate', 'payamount', 'paytype', 'journalid' ), 'classes': ('collapse',)})]
    raw_id_fields = ['memberid']

class DuesInline(admin.TabularInline) :
    model         = Dues
#   fieldsets     = [('Dues paid', {'fields': ('paydate', 'payamount', 'paytype', 'journalid' ), 'classes': ('collapse',)})]
    raw_id_fields = ['journalid']
    extra         = 1

class JournalInline(admin.TabularInline) :
    model         = Journal
#   fieldsets     = [('Journal Entries', {'fields': ('entrydate', 'entrytype', 'comment'), 'classes': ('collapse',)})]
    raw_id_fields = ['memberid']
    extra         = 1

class MemberAdmin(admin.ModelAdmin) :
    search_fields = ['last', 'first', 'middle', 'salute', 'suffix']
    list_display  = ['memberid', 'first', 'middle', 'last', 'mailadr', 'emailadr']
    list_editable = []
    list_filter   = ['mailadr']
    list_per_page = 35
    save_on_top   = True
    fieldsets     = [(None, {'fields': (('salute', 'first', 'middle', 'last', 'suffix'), 'mailadr', 'emailadr', 'telnumber')})]
    inlines       = [PrefsInline, DuesInline, JournalInline]
    
admin.site.register(Member, MemberAdmin)

class MemberInline(admin.TabularInline) :
    model = Member
    raw_id_fields = ['mailadr', 'emailadr', 'telnumber']
    extra         = 1

class MailAddressAdmin(admin.ModelAdmin) :
    search_fields = ['street', 'city', 'zipcode', 'zipext', 'company']
    fieldsets = [(None, {'fields': ('company', ('street', 'aptnum'), ('city', 'state', 'zipcode', 'zipext'))})]
    inlines   = [MemberInline]
    
admin.site.register(MailAddress, MailAddressAdmin)

class EMailAddressAdmin(admin.ModelAdmin) :
    search_fields = ['name', 'domain']
    fieldsets = [(None,{'fields': ('name', 'domain')})]
    inlines   = [MemberInline]
    
admin.site.register(EMailAddress, EMailAddressAdmin)

class TelNumberAdmin(admin.ModelAdmin) :
    search_fields = ['area', 'exch', 'number']
    fieldsets = [(None,{'fields': ('area', 'exch', 'number', 'ext')})]
    inlines   = [MemberInline]
    
admin.site.register(TelNumber, TelNumberAdmin)

