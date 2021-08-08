#! /usr/bin/python
"""
forms.py
Classes furnishing forms for the membermanage web application 
"""
from django                             import forms
from django.core.urlresolvers           import reverse
from fidoonline.membermanage.models     import MailAddress, TelNumber, EMailAddress, Member, MemberPet, Pet, DogTag, MemberPreference, Journal, Dues
# import pydb

class DuesForm (forms.Form) :
    df_paytype = forms.ChoiceField (required=True, label='Type of payment', help_text='Choose an appropriate payment type.', choices=Dues.paytypes)
    df_amount  = forms.DecimalField(required=True, label='Amount',          help_text='Enter payment amount.')
    # --------------------------------------------------------------------------------
    def getStatusFlags(self) :
        """
        return 0 - amount and pay type populated 1- No amount 2 - No paytype 3 - Both amount and paytype absent
        """

        if len(self.cleaned_data) :
            return   int(not self.cleaned_data.has_key('df_paytype') or not hasattr(self.cleaned_data['df_paytype'], '__len__')) * 2 +  \
                     int(not self.cleaned_data.has_key('df_amount')  or not hasattr(self.cleaned_data['df_amount'], '__float__'))
        else :
            return 3
    # --------------------------------------------------------------------------------
    def clean(self) :
        """
        """
        import decimal

        status = self.getStatusFlags()
        msg    = ["", \
                  "Expected dollar-and-cents entry for dues payment. (Omit leading currency symbols like '$').", \
                  "Expected dollar-and-cents entry for dues payment. (Omit leading currency symbols like '$').", \
                  "Enter a dollar-and-cents entry for dues payment with no leading currency symbol."  \
                 ][status]  
        if status == 0 :
            try :
                damt = self.cleaned_data['df_amount']
            except decimal.InvalidOperation:
                raise forms.ValidationError(msg)
            if damt <  decimal.Decimal('5.00') :
                raise forms.ValidationError("A FIDO Dues Payment should be no less than 5.00 (as of July, 2010).")
            return self.cleaned_data
        else :
            raise forms.ValidationError(msg)
        
class EMailAddressForm(forms.Form) :
    em_name    = forms.CharField(required=True, label = 'Name',   help_text='The mailbox name', widget=forms.TextInput(attrs={'maxlength':30, 'size':20}))   
    em_domain  = forms.CharField(required=True, label = 'Domain', help_text='The mail server\'s domain',  widget=forms.TextInput(attrs={'maxlength':30, 'size':20}))
    # --------------------------------------------------------------------------------
    def getStatusFlags(self) :
        """
        return 0 - name and domain populated 1- No domain 2 - No name 3 - Both name and domain missing
        """
        if len(self.cleaned_data) :
            return   int(hasattr(self.cleaned_data['em_name'],   '__len__') and len(self.cleaned_data['em_name'])   == 0)*2 +  \
                     int(hasattr(self.cleaned_data['em_domain'], '__len__') and len(self.cleaned_data['em_domain']) == 0)
        else :
            return -1
    # --------------------------------------------------------------------------------
    def clean(self) :
        """
        """
        edx = self.getStatusFlags()
        if edx == 1 or edx == 2 :
            msg = ['', 'Missing domain name', 'Missing mailbox name', 'No domain or mailbox named'][edx]
            raise forms.ValidationError(msg)
        else :
            return self.cleaned_data
    
class EmptyForm (forms.Form):
    pass

class JournalForm (forms.Form) :
    jf_subject = forms.ChoiceField(required=True, label='Subject', help_text='Choose a subject most appropriate for the entry.', choices=(
                                                                                                                                           ('Address',        'Postal address changes'),
                                                                                                                                           ('Correspondence', 'Text of member letters to FIDO'),
                                                                                                                                           ('Deletion',       'Member slated for deletion'),
                                                                                                                                           ('Payment',        'Payment identifiers'),
                                                                                                                                           ('EMail',          'EMail changes'),
                                                                                                                                           ('Identity',       'Member name changes'),
                                                                                                                                           ('Mailing',        'Mailings to members'),
                                                                                                                                           ('Pet',            'Changes to pet\'s name, tag or description'),
                                                                                                                                           ('Preference',     'Member preference change'),
                                                                                                                                           ('Remark',         'Non-specific matter'),
                                                                                                                                           ('Telephone',      'New or changed phones')
                                                                                                                                         )
                                  )
    jf_comment = forms.CharField(required=True,   label='Comment', help_text='Enter particular notes or explanations.', widget=forms.Textarea(attrs={'cols':45, 'wrap':'soft', 'rows': 4}))
    # -------------------------------------------------------------------------------------
    def getStatusFlags(self) :
        """
        return 0 - comment and subject populated 1- No comment 2 - No subject 3 - Both comment and subject absent
        """
        if len(self.cleaned_data) :
            return   int(not self.cleaned_data.has_key('jf_subject') or not hasattr(self.cleaned_data['jf_subject'], '__len__')) * 2 +  \
                     int(not self.cleaned_data.has_key('jf_comment') or not hasattr(self.cleaned_data['jf_comment'], '__len__'))
        else :
            return 3
    # -------------------------------------------------------------------------------------
    def clean(self) :
        ck  = self.getStatusFlags()
        msg = [
                "",
                "Comment should be a brief description of the subject; for payments describe the method of payment and description of the instrument.",
                "Choose a standard journal subject. ('Address', 'Correspondence', 'Payment', 'EMail', 'Identity', 'Mailing', 'Pet', 'Preference', 'Remark', 'Telephone')",
                "Form seems to have no recognizable content."
              ][ck]
        if ck == 0 :
            if len(self.cleaned_data['jf_comment']) == 0 :
                raise ValidationError("Please enter a comment furnishing particular details. For payments, describe method of payment and identifying aspects of checks or money orders.")  
            return self.cleaned_data
        else :
            raise forms.ValidationError(msg)
        
class Lookup (forms.Form) :
    lu_search   = forms.CharField(max_length=70, required=False, label='Name Lookup', help_text='Enter a few letters; case does not matter.', widget=forms.TextInput(attrs={'style':'opacity:1.0;filter:alpha(opacity=100,style=0)','size':'10'}))
    searchagent = '/member/directory/'
    newagent    = '/member/detail/new/'
    
class MailAddressForm(forms.ModelForm) :
    class Meta :
        model  = MailAddress
        fields = ('company', 'street', 'aptnum', 'city', 'state', 'zipcode', 'zipext')
    # -------------------------------------------------------------------------------------    
    def getStatusFlags (self) :    
        return       (
                        1 * (self.cleaned_data.get('street') != None and bool(len(self.cleaned_data.get('street')))  and not self._errors.has_key('street'))  +
                        2 * (self.cleaned_data.get('city')   != None and bool(len(self.cleaned_data.get('city')))    and not self._errors.has_key('city'))    +
                        4 * (self.cleaned_data.get('state')  != None and bool(len(self.cleaned_data.get('state')))   and not self._errors.has_key('state'))   +
                        8 * (self.cleaned_data.get('zipcode')!= None and bool(len(self.cleaned_data.get('zipcode'))) and not self._errors.has_key('zipcode')) +
                       16 * (self.cleaned_data.get('zipext') != None and bool(len(self.cleaned_data.get('zipext')))  and not self._errors.has_key('zipext'))
                     )
    # -------------------------------------------------------------------------------------    
    def clean(self) :
        """
        validation rule: street, city, state, zipcode and zipext must be non-zero length strings.
        indicate particular fields that are in error if the overall validation rule fails.
        """
        from django.forms.util import ErrorList
        # ---------------------------------------------------------------------------------
        def ma_00 (err) :
            return True
        # ---------------------------------------------------------------------------------
        def ma_01 (err) :
            if not err.has_key('street') :
                err['street'] = ErrorList()
            err['street'].append('Enter full street address')
            return False 
        # ---------------------------------------------------------------------------------
        def ma_02 (err) :
            if not err.has_key('city') :
                err['city'] = ErrorList()
            err['city'].append('Enter a city name')
            return False 
        # ---------------------------------------------------------------------------------
        def ma_03 (err) :
            pass
            if not err.has_key('street') :
                err['street'] = ErrorList()
            err['street'].append('Enter full street address')
            if not err.has_key('city') :
                err['city'] = ErrorList()
            err['city'].append('Enter a city name')
            return False 
        # ---------------------------------------------------------------------------------
        def ma_04 (err) :
            if not err.has_key('state') :
                err['state'] = ErrorList()
            err['state'].append('Enter a two letter state code')
            return False 
        # ---------------------------------------------------------------------------------
        def ma_05 (err) :
            if not err.has_key('street') :
                err['street'] = ErrorList()
            err['street'].append('Enter full street address')
            if not err.has_key('state') :
                err['state'] = ErrorList()
            err['state'].append('Enter a two letter state code')
            return False 
        # ---------------------------------------------------------------------------------
        def ma_06 (err) :
            if not err.has_key('city') :
                err['city'] = ErrorList()
            err['city'].append('Enter a city name')
            if not err.has_key('state') :
                err['state'] = ErrorList()
            err['state'].append('Enter a two letter state code')
            return False
        # ---------------------------------------------------------------------------------
        def ma_07 (err) :
            if not err.has_key('street') :
                err['street'] = ErrorList()
            err['street'].append('Enter full street address')
            if not err.has_key('city') :
                err['city'] = ErrorList()
            err['city'].append('Enter a city name')
            if not err.has_key('state') :
                err['state'] = ErrorList()
            err['state'].append('Enter a two letter state code')
            return False
        # ---------------------------------------------------------------------------------
        def ma_08 (err) :
            if not err.has_key('zipcode') :
                err['zipcode'] = ErrorList()
            err['zipcode'].append('Enter a five digit ZIP code')
            return False
        # ---------------------------------------------------------------------------------
        def ma_09 (err) :
            if not err.has_key('street') :
                err['street'] = ErrorList()
            err['street'].append('Enter full street address')
            if not err.has_key('zipcode') :
                err['zipcode'] = ErrorList()
            err['zipcode'].append('Enter a five digit ZIP code')
            return False
        # ---------------------------------------------------------------------------------
        def ma_0a (err) :
            if not err.has_key('city') :
                err['city'] = ErrorList()
            err['city'].append('Enter a city name')
            if not err.has_key('zipcode') :
                err['zipcode'] = ErrorList()
            err['zipcode'].append('Enter a five digit ZIP code')
            return False
        # ---------------------------------------------------------------------------------
        def ma_0b (err) :
            if not err.has_key('street') :
                err['street'] = ErrorList()
            err['street'].append('Enter full street address')
            if not err.has_key('city') :
                err['city'] = ErrorList()
            err['city'].append('Enter a city name')
            if not err.has_key('zipcode') :
                err['zipcode'] = ErrorList()
            err['zipcode'].append('Enter a five digit ZIP code')
            return False
        # ---------------------------------------------------------------------------------
        def ma_0c (err) :
            if not err.has_key('state') :
                err['state'] = ErrorList()
            err['state'].append('Enter a two letter state code')
            if not err.has_key('zipcode') :
                err['zipcode'] = ErrorList()
            err['zipcode'].append('Enter a five digit ZIP code')
            return False
        # ---------------------------------------------------------------------------------
        def ma_0d (err) : 
            if not err.has_key('street') :
                err['street'] = ErrorList()
            err['street'].append('Enter full street address')
            if not err.has_key('state') :
                err['state'] = ErrorList()
            err['state'].append('Enter a two letter state code')
            if not err.has_key('zipcode') :
                err['zipcode'] = ErrorList()
            err['zipcode'].append('Enter a five digit ZIP code')
            return False
        # ---------------------------------------------------------------------------------
        def ma_0e (err) :
            if not err.has_key('city') :
                err['city'] = ErrorList()
            err['city'].append('Enter a city name')
            if not err.has_key('state') :
                err['state'] = ErrorList()
            err['state'].append('Enter a two letter state code')
            if not err.has_key('zipcode') :
                err['zipcode'] = ErrorList()
            err['zipcode'].append('Enter a five digit ZIP code')
            return False
        # ---------------------------------------------------------------------------------
        def ma_0f (err) :
            if not err.has_key('street') :
                err['street'] = ErrorList()
            err['street'].append('Enter full street address')
            if not err.has_key('city') :
                err['city'] = ErrorList()
            err['city'].append('Enter a city name')
            if not err.has_key('state') :
                err['state'] = ErrorList()
            err['state'].append('Enter a two letter state code')
            if not err.has_key('zipcode') :
                err['zipcode'] = ErrorList()
            err['zipcode'].append('Enter a five digit ZIP code')
            return False
        # ---------------------------------------------------------------------------------
        def ma_10 (err) :
            if not err.has_key('zipext') :
                err['zipext'] = ErrorList()
            err['zipext'].append('Enter a ZIP+4 code')
            return False
        # ---------------------------------------------------------------------------------
        def ma_11 (err) :
            if not err.has_key('street') :
                err['street'] = ErrorList()
            err['street'].append('Enter full street address')
            if not err.has_key('zipext') :
                err['zipext'] = ErrorList()
            err['zipext'].append('Enter a ZIP+4 code')
            return False
        # ---------------------------------------------------------------------------------
        def ma_12 (err) :
            if not err.has_key('city') :
                err['city'] = ErrorList()
            err['city'].append('Enter a city name')
            if not err.has_key('zipext') :
                err['zipext'] = ErrorList()
            err['zipext'].append('Enter a ZIP+4 code')
            return False
        # ---------------------------------------------------------------------------------
        def ma_13 (err) :
            if not err.has_key('street') :
                err['street'] = ErrorList()
            err['street'].append('Enter full street address')
            if not err.has_key('city') :
                err['city'] = ErrorList()
            err['city'].append('Enter a city name')
            if not err.has_key('zipext') :
                err['zipext'] = ErrorList()
            err['zipext'].append('Enter a ZIP+4 code')
            return False
        # ---------------------------------------------------------------------------------
        def ma_14 (err) :
            if not err.has_key('state') :
                err['state'] = ErrorList()
            err['state'].append('Enter a two letter state code')
            if not err.has_key('zipext') :
                err['zipext'] = ErrorList()
            err['zipext'].append('Enter a ZIP+4 code')
            return False
        # ---------------------------------------------------------------------------------
        def ma_15 (err) :
            if not err.has_key('street') :
                err['street'] = ErrorList()
            err['street'].append('Enter full street address')
            if not err.has_key('state') :
                err['state'] = ErrorList()
            err['state'].append('Enter a two letter state code')
            if not err.has_key('zipext') :
                err['zipext'] = ErrorList()
            err['zipext'].append('Enter a ZIP+4 code')
            return False
        # ---------------------------------------------------------------------------------
        def ma_16 (err) :
            if not err.has_key('city') :
                err['city'] = ErrorList()
            err['city'].append('Enter a city name')
            if not err.has_key('state') :
                err['state'] = ErrorList()
            err['state'].append('Enter a two letter state code')
            if not err.has_key('zipext') :
                err['zipext'] = ErrorList()
            err['zipext'].append('Enter a ZIP+4 code')
            return False
        # ---------------------------------------------------------------------------------
        def ma_17 (err) :
            if not err.has_key('street') :
                err['street'] = ErrorList()
            err['street'].append('Enter full street address')
            if not err.has_key('city') :
                err['city'] = ErrorList()
            err['city'].append('Enter a city name')
            if not err.has_key('state') :
                err['state'] = ErrorList()
            err['state'].append('Enter a two letter state code')
            if not err.has_key('zipext') :
                err['zipext'] = ErrorList()
            err['zipext'].append('Enter a ZIP+4 code')
            return False
        # ---------------------------------------------------------------------------------
        def ma_18 (err) :
            if not err.has_key('zipcode') :
                err['zipcode'] = ErrorList()
            err['zipcode'].append('Enter a five digit ZIP code')
            if not err.has_key('zipext') :
                err['zipext'] = ErrorList()
            err['zipext'].append('Enter a ZIP+4 code')
            return False
        # ---------------------------------------------------------------------------------
        def ma_19 (err) :
            if not err.has_key('street') :
                err['street'] = ErrorList()
            err['street'].append('Enter full street address')
            if not err.has_key('zipcode') :
                err['zipcode'] = ErrorList()
            err['zipcode'].append('Enter a five digit ZIP code')
            if not err.has_key('zipext') :
                err['zipext'] = ErrorList()
            err['zipext'].append('Enter a ZIP+4 code')
            return False
        # ---------------------------------------------------------------------------------
        def ma_1a (err) :
            if not err.has_key('city') :
                err['city'] = ErrorList()
            err['city'].append('Enter a city name')
            if not err.has_key('zipcode') :
                err['zipcode'] = ErrorList()
            err['zipcode'].append('Enter a five digit ZIP code')
            if not err.has_key('zipext') :
                err['zipext'] = ErrorList()
            err['zipext'].append('Enter a ZIP+4 code')
            return False
        # ---------------------------------------------------------------------------------
        def ma_1b (err) :
            if not err.has_key('street') :
                err['street'] = ErrorList()
            err['street'].append('Enter full street address')
            if not err.has_key('city') :
                err['city'] = ErrorList()
            err['city'].append('Enter a city name')
            if not err.has_key('zipcode') :
                err['zipcode'] = ErrorList()
            err['zipcode'].append('Enter a five digit ZIP code')
            if not err.has_key('zipext') :
                err['zipext'] = ErrorList()
            err['zipext'].append('Enter a ZIP+4 code')
            return False
        # ---------------------------------------------------------------------------------
        def ma_1c (err) :
            if not err.has_key('city') :
                err['city'] = ErrorList()
            err['city'].append('Enter a city name')
            if not err.has_key('state') :
                err['state'] = ErrorList()
            err['state'].append('Enter a two letter state code')
            if not err.has_key('zipext') :
                err['zipext'] = ErrorList()
            err['zipext'].append('Enter a ZIP+4 code')
            return False
        # ---------------------------------------------------------------------------------
        def ma_1d (err) :
            if not err.has_key('street') :
                err['street'] = ErrorList()
            err['street'].append('Enter full street address')
            if not err.has_key('state') :
                err['state'] = ErrorList()
            err['state'].append('Enter a two letter state code')
            if not err.has_key('zipcode') :
                err['zipcode'] = ErrorList()
            err['zipcode'].append('Enter a five digit ZIP code')
            if not err.has_key('zipext') :
                err['zipext'] = ErrorList()
            err['zipext'].append('Enter a ZIP+4 code')
            return False
        # ---------------------------------------------------------------------------------
        def ma_1e (err) :
            if not err.has_key('city') :
                err['city'] = ErrorList()
            err['city'].append('Enter a city name')
            if not err.has_key('state') :
                err['state'] = ErrorList()
            err['state'].append('Enter a two letter state code')
            if not err.has_key('zipcode') :
                err['zipcode'] = ErrorList()
            err['zipcode'].append('Enter a five digit ZIP code')
            if not err.has_key('zipext') :
                err['zipext'] = ErrorList()
            err['zipext'].append('Enter a ZIP+4 code')
            return False
        # ---------------------------------------------------------------------------------
        def ma_1f (err) :
            err = {}
            return True
        # ---------------------------------------------------------------------------------
        ef = [
               ma_00, # nothing at all.
               ma_01, # street address.
               ma_02, # city.
               ma_03, # street address and city.
               ma_04, # state.
               ma_05, # street address and state.
               ma_06, # city and state.
               ma_07, # street, city and state.
               ma_08, # zipcode
               ma_09, # street address and zipcode
               ma_0a, # city and zipcode
               ma_0b, # street, city and zipcode
               ma_0c, # state and zipcode
               ma_0d, # street, state and zipcode
               ma_0e, # city, state, and zipcode
               ma_0f, # street, city, state, and zipcode
               ma_10, # zipext.
               ma_11, # street address and zipext.
               ma_12, # city.
               ma_13, # street address, city and zipext.
               ma_14, # state.
               ma_15, # street address, state and zipext.
               ma_16, # city, state and zipext.
               ma_17, # street, city, state and zipext.
               ma_18, # zipcode and zipext.
               ma_19, # street address, zipcode and zipext.
               ma_1a, # city, zipcode and zipext.
               ma_1b, # street, city, zipcode and zipext.
               ma_1c, # state, zipcode and zipext.
               ma_1d, # street, state, zipcode, and zipext.
               ma_1e, # city, state, zipcode and zipext.
               ma_1f, # street, city, state, zipcode, and zipext
              ][31 - self.getStatusFlags()](self._errors)
        if not ef :
            raise forms.ValidationError('The street address does not seem to be complete: %s' % (", ".join(self.non_field_errors())))
        else :
            if self._errors :
                self._errors = {}
            return self.cleaned_data        
        # ---------------------------------------------------------------------------------

class MemberForm(forms.Form) :
    mf_salute  = forms.ChoiceField(choices = (('', ''), ('Dr.', 'Dr.'), ('Hon', 'Hon'), ('Miss','Miss'), ('Mr.',  'Mr.'), ('Mrs.', 'Mrs.'), ('Ms.',  'Ms'), ('Sir',  'Sir')), label = 'Salut.', required=False, help_text='Title or formal salutation')
    mf_first   = forms.CharField(required=True,  label = 'First',  help_text='Member\'s personal name', widget=forms.TextInput(attrs={'maxlength':40, 'size':20}))   
    mf_middle  = forms.CharField(required=False, label = 'Middle', help_text='Middle name or initial',  widget=forms.TextInput(attrs={'maxlength':40, 'size':10}))   
    mf_last    = forms.CharField(required=True,  label = 'Last',   help_text='Member\'s family name',   widget=forms.TextInput(attrs={'maxlength':40, 'size':20}))   
    mf_suffix  = forms.CharField(required=False, label = 'Suffix', help_text='Affiliation or degree',   widget=forms.TextInput(attrs={'maxlength':40, 'size':2}))
    
class PetForm (forms.Form) :
    pf_name    = forms.CharField(required=True,  label='Name',        help_text='Pet\'s name.',                                                                             widget=forms.TextInput(attrs={'maxlength':10, 'size':10}))
    pf_desc    = forms.CharField(required=False, label='Description', help_text='Enter distinguishing characteristics or features. Leave blank if such are not available.', widget=forms.Textarea(attrs={'cols':42, 'wrap':'soft', 'rows':2}))
    # ---------------------------------------------------------------------------------
    def getStatusFlags(self) :
        """
        return 0 - name, dog tag and description present
               1 - No description
               2 - No dog name
               3 - No dog name or description 
        """
        if len(self.cleaned_data) > 0 :
            return   int(not self.cleaned_data.has_key('pf_name') or len(self.cleaned_data['pf_name']) == 0)*2 +  \
                     int(not self.cleaned_data.has_key('pf_desc') or len(self.cleaned_data['pf_desc']) == 0)
        else :
            return 3
    # ---------------------------------------------------------------------------------
    def clean (self) :
        """
        Name must be present, the description need not be. Reject an entry without a name.
        """
        msg   = 'Need a Pet name and description - The name is mandatory, but the description is optional.'
        ck    = self.getStatusFlags()
        if ck < 2 :
            return self.cleaned_data
        else :
            raise forms.ValidationError ( msg )

class TagForm(forms.Form) :
    ta_number = forms.IntegerField(min_value=1, max_value=999999, required=True,  label = 'Dog Tag Number', help_text='Enter the FIDO dog tag number stamped on the tag.',   widget=forms.TextInput(attrs={'maxlength':10, 'size':15}))
    # ---------------------------------------------------------------------------------
    def getStatusFlags(self) :
        """
        return 0 - dog tag number is present
               1 - No dog tag number
        """
        return int(not self.cleaned_data.has_key('ta_number') or not hasattr(self.cleaned_data['ta_number'], '__int__'))
    # ---------------------------------------------------------------------------------
    def clean (self) :
        """
        Number must be present and unassigned.
        """

        msg   = 'Please furnish a tag number (as stamped on the tag itself).'
        ck = self.getStatusFlags()
        if ck == 0 :
            try :
                priordogtag = DogTag.objects.get(pk=self.cleaned_data['ta_number'])
            except DogTag.DoesNotExist :
                priordogtag = None
            if priordogtag :
                mstr      = ""
                pet_qs    = Pet.objects.filter(dogtag__exact=priordogtag)
                member_qs = Member.objects.filter(memberpet__pet__dogtag__exact=priordogtag)
                if member_qs.count() :
                    for mbr in member_qs :
                        mstr = "%s %s" % (mstr, "%s %s" % (mbr.first, mbr.last)) 
                email  = unicode(member_qs[0].emailadr)
                if email != 'None' :
                    raise forms.ValidationError("Possible tag misassignment: Tag: %06d has been assigned to %s, belonging to %s. Please email <a href='mailto:%s'>%s</a> and ask what tag %s really has." % (priordogtag.tagnumber, pet_qs[0].name, mstr, email, email, pet_qs[0].name))
                else :
                    raise forms.ValidationError("Possible tag misassignment: Tag: %06d has been assigned to %s, belonging to %s. Please contact %s and ask what tag they really have for %s." % (priordogtag.tagnumber, pet_qs[0].name, mstr, mstr, pet_qs[0].name))
            else :
                return self.cleaned_data
        else :
            raise forms.ValidationError ( msg )
        
class TelNumberForm(forms.Form) : 
    tf_area = forms.CharField(min_length=3, max_length=3, required=False,  label = 'Area code', help_text='Area code',   widget=forms.TextInput(attrs={'maxlength':3, 'size':2}))
    tf_exch = forms.CharField(min_length=3, max_length=3, required=False,  label = 'Exchange',  help_text='Exchange',    widget=forms.TextInput(attrs={'maxlength':3, 'size':2}))
    tf_line = forms.CharField(min_length=4, max_length=4, required=False,  label = 'Number',    help_text='Line number', widget=forms.TextInput(attrs={'maxlength':4, 'size':3}))
    tf_ext  = forms.CharField(min_length=0, max_length=4, required=False,  label = 'Extension', help_text='Extension',   widget=forms.TextInput(attrs={'maxlength':4, 'size':3}))
    # ---------------------------------------------------------------------------------
    def clean (self) :
        """
        1. Success if <Areacode><exchangecode><linenumber><extension> are digits.
        2. Success if <Areacode><exchangecode><linenumber> are digits and <extension> is empty.
        3. Sucesss if <Areacode><exchangecode><linenumber><extension> are all empty.
        4. Fail if any <Areacode><exchangecode><linenumber> are empty but not all empty (see 3).
        5. Fail if any <Areacode><exchangecode><linenumber><extension> are non-digit
        """
        # -----------------------------------------------------------------------------

        def getStatusFlags () :
            """
            <Areacode><exchangecode><linenumber><extension> Four 1 bit flags. Flag is SET
            if the corresponding part of the telephone number is not digit (empty string is 'not digit'). Returns
            15 for a completely undigital unspecified telephone number, 0 for when all fields have digit text.
            """
            if len(self.cleaned_data) > 0 :
                return   int(hasattr(self.cleaned_data['tf_area'], 'isdigit') and self.cleaned_data['tf_area'].isdigit() == False)*8 +  \
                         int(hasattr(self.cleaned_data['tf_exch'], 'isdigit') and self.cleaned_data['tf_exch'].isdigit() == False)*4 +  \
                         int(hasattr(self.cleaned_data['tf_line'], 'isdigit') and self.cleaned_data['tf_line'].isdigit() == False)*2 +  \
                         int(hasattr(self.cleaned_data['tf_ext'],  'isdigit') and self.cleaned_data['tf_ext'].isdigit()  == False)
            else :
                return 15 
        # -----------------------------------------------------------------------------
        def todigital(phone_dict) :
            """
            for each phone_dict entry :  string-of-digits   -> Decimal
                                         zero-length-string -> None
            """
            # -------------------------------------------------------------------------
            def item_to_digital (digitstring) :
                """
                Make a decimal if string has length, otherwise return None
                """
                import decimal
                if hasattr(digitstring, '__len__') and len(digitstring) > 0 :
                    try :
                        return decimal.Decimal(digitstring)
                    except decimal.InvalidOperation, ex :
                        raise forms.ValidationError, "TelNumberForm is not catching non-digit strings correctly. Got %s." % (digitstring)
                else :
                    return None

            for k in phone_dict.keys() :
                phone_dict[k] = item_to_digital(phone_dict[k])
            return phone_dict    

        msg = 'Cannot recognize phone number.'
        if  len(self.cleaned_data) > 0 :
            if  self.cleaned_data.has_key('tf_area') and self.cleaned_data['tf_area'] != None and \
                self.cleaned_data.has_key('tf_exch') and self.cleaned_data['tf_exch'] != None and \
                self.cleaned_data.has_key('tf_line') and self.cleaned_data['tf_line'] != None and \
                self.cleaned_data.has_key('tf_line') and self.cleaned_data['tf_line'] != None :
                ec = getStatusFlags()
                if ec == 0 :
                    return todigital(self.cleaned_data) # Case 1.
                elif ec == 1:
                    if hasattr(self.cleaned_data['tf_ext'], '__len__') and len(self.cleaned_data['tf_ext']) == 0 :
                        return todigital(self.cleaned_data) # Case 2.
                    else :
                        raise forms.ValidationError, msg # Type of Case 5: all but extension are digit, but extension is non-empty and not digit.
                elif hasattr(self.cleaned_data['tf_area'], '__len__') and len(self.cleaned_data['tf_area']) == 0 and \
                     hasattr(self.cleaned_data['tf_exch'], '__len__') and len(self.cleaned_data['tf_exch']) == 0 and \
                     hasattr(self.cleaned_data['tf_line'], '__len__') and len(self.cleaned_data['tf_line']) == 0 and \
                     hasattr(self.cleaned_data['tf_ext'],  '__len__') and len(self.cleaned_data['tf_ext' ]) == 0 :
                    return todigital(self.cleaned_data) # Case 3: User is explicitly indicating a phone number is not available by leaving all fields empty.
                else :
                    raise forms.ValidationError, msg # Case 4 or 5; who care which one ?
            else :
                raise forms.ValidationError, msg # Missing fields
        else :    
            raise forms.ValidationError, msg # Data are dirty: no clean fields
