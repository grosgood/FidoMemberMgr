"""
views.py
HTTP request object processors for the membermanage application.
"""
from django                             import forms
from django.contrib.auth.decorators     import login_required
from django.core.urlresolvers           import reverse
from django.db                          import transaction
from django.forms.util                  import ErrorList
from django.http                        import HttpResponseRedirect, HttpResponse
from django.shortcuts                   import render_to_response, get_object_or_404
from fidoonline.membermanage.forms      import DuesForm, EMailAddressForm, EmptyForm, JournalForm, Lookup, MailAddressForm, MemberForm, PetForm, TelNumberForm
from fidoonline.membermanage.models     import DogTag, Dues, EMailAddress, Journal, MailAddress, Member, MemberPet, MemberPreference, Pet, TelNumber 
from fidoonline.membermanage.memberutil import getstatusstyle
# import pydb
# -------------------------------------------------------------------------------------
@login_required
def memberlist(req) :
    """
    Build an overview list of the membership, to be rendered through the mlist.html template.
    The request object may have a POST field with a search component; this component will be a
    string to filter both first and last names 
    req: HTTP request object
    """
    from django.db.models import Q
    
    headers = (
               {'name': 'Member',         'width': 190},
               {'name': 'Street',         'width': 190},
               {'name': 'City',           'width': 120},
               {'name': 'ST',             'width':  30},
               {'name': 'Zipcode',        'width':  85},
               {'name': 'Telephone',      'width':  90},
               {'name': 'Email',          'width': 230},
               {'name': 'Status',         'width': 100}
              ) 
    names = []
    if(req.method == "POST") :
        lookup   = Lookup(req.POST)
        if lookup.is_valid() :
            fstring = lookup.cleaned_data['lu_search']
            members = Member.objects.filter(Q(first__icontains=fstring) | Q(last__icontains=fstring))
        else :
            members = Member.objects.all()
    else :
        members  = Member.objects.all()
        lookup   = Lookup()
    for m in members :
        m.stat = 0
        if not (hasattr(m, 'mailadr')) or m.mailadr == None :
            m.stat += 1
            m.mailadr = MailAddress(company=' ', aptnum=' ', street=' ', state=' ', zipcode=' ', zipext=' ', country=' ')
        m.stat *= 2
        if not (hasattr(m, 'emailadr')) or m.emailadr == None :
            m.stat += 1
            m.emailadr = EMailAddress(name=' ', domain=' ')
        m.stat *= 2    
        if not (hasattr(m, 'telnumber')) or m.telnumber == None :
            m.stat += 1
            m.telnumber = TelNumber(area=0, exch=0, number=0, ext=0)
                
        strng = []
        for i in (m.salute, m.first, m.middle, m.last, m.suffix) :
            if len(i) : strng.append(i)
        if m.stat & 1 :
            telnum = ' '
        else :    
            telnum = '-'.join(("%03d" % (m.telnumber.area), "%03d" % (m.telnumber.exch), "%04d" % (m.telnumber.number)))
            if m.telnumber.ext > 0 :
                telnum += telnum + " ext: %d" % (m.telnumber.ext)
        crumbs     = ({'label': 'Start Here', 'link': reverse('fidoonline.membermanage.starthereview.start')}, {'label': 'Member Directory', 'link': None})    
        names.append(
                       {
                          'identifier'    : m.memberid,
                          'name'          : ' '.join(strng),
                          'mailadr'       : {
                                              'identifier' : m.mailadr.adrid,
                                              'street'     : m.mailadr.street,
                                              'city'       : m.mailadr.city,
                                              'state'      : m.mailadr.state,
                                              'zipcode'    : "%s-%s" % (m.mailadr.zipcode, m.mailadr.zipext),
                                              'err'        : False
                                            },
                          'telephone'     : {'number'  :telnum, 'err' : False},
                          'email'         : {'address' :"%s@%s" % (m.emailadr.name, m.emailadr.domain), 'err' : False},
                          'status'        : {'expiry'  : "%5d" % (m.term['expiry']), 'style' : getstatusstyle(m)}
                       } 
                    )
        if m.stat & 1 :
            names[-1]['telephone']['err'] = True
        if m.stat & 2 :
            names[-1]['email']['err']     = True
        if m.stat & 4 :
            names[-1]['mailadr']['err']   = True
    return render_to_response('membermanage/mlist.html', { 'crumbline' : crumbs, 'lookup': lookup, 'member_names': names, 'table_headers': headers, 'window_title': "Membership Matters", 'page_title': 'Membership Directory',  })
# -------------------------------------------------------------------------------------
@login_required
def createonemember (req) :
    """
    The request object is asking for an unpopulated member entry
    form. Pass through to detail a member who is as yet a non-entity
    req: HTTP request object
    """
    return detailonemember(req, None)
# -------------------------------------------------------------------------------------
@login_required
def detailonemember (req, member_id) :
    """
    On initial receipt, return a form populated with member information from the database
    """
    formdict = {
                'address_form': None,
                'd_entries'   : None,
                'd_form'      : None,
                'email_form'  : None,
                'j_entries'   : None,
                'j_form'      : None,
                'lookup'      : None,
                'member_form' : None,
                'member_id'   : None,
                'p_entries'   : None,
                'p_form'      : None,
                'page_title'  : None,
                'pref_flags'  : None,
                'r_entry'     : None,
                'telnum_form' : None,
                'window_title': None
               }  
    
    if req.method == "POST" :
        # Have been handed an altered form that may update member data
        return processmemberpost(req, member_id, formdict)
    elif member_id != None  :
        # Furnishing details about a member with the given member ID
        providememberdata(member_id, formdict)
    else :
        # Asking for a blank form
        initializememberform(formdict) 
        
    return render_to_response('membermanage/formbase.html', formdict) 
# -------------------------------------------------------------------------------------
def initializememberform(formdict) :
    """
    Adding new member. Initialize form. 
    """
    pdict   = dict(MemberPreference.prefclasses)
    prefset = EmptyForm()
    for c in pdict.iterkeys() :
        prefset.fields[c] = forms.BooleanField(required=False, label=pdict[c], help_text='Check the box to request this service.')
        prefset.fields[c].initial = False
    formdict['address_form'] = MailAddressForm()
    formdict['d_form']       = DuesForm()
    formdict['email_form']   = EMailAddressForm()
    formdict['form_error']   = ErrorList()
    formdict['j_form']       = JournalForm()
    formdict['lookup']       = Lookup()
    formdict['member_form']  = MemberForm()
    formdict['member_id']    = "new"
    formdict['p_form']       = PetForm() 
    formdict['page_title']   = "New Member Entry"
    formdict['pref_flags']   = prefset
    formdict['telnum_form']  = TelNumberForm()
    formdict['window_title'] = "New Member Entry" 
# -------------------------------------------------------------------------------------
@transaction.commit_manually
def processmemberpost (req, member_id, formdict) :
    """
    Have been handed an altered form that may update member data
    req:       an HTTP request object with a somewhat, semi, maybe completely populated or screwed up POST component
    member_id: stringified member ID or the None (null) object
    formdict:  the dictionary map of formbase.html, detailing the data concerning one member
    """
    from django.http import HttpResponseRedirect, HttpResponse
    from django.db.models import Q
    import datetime as dt
    import decimal

    # --------------------------------------------------------------------------------    
    def _updateformsec(map, dat_dict, form_dict) :
        """
        """
        for df, ff in map.iteritems() :
            dat_dict.__dict__[df] = form_dict.cleaned_data[ff]

    # --------------------------------------------------------------------------------
    def _dup(ad, bd, checkfields=None) :
        """
        """
        if hasattr(ad, '__dict__') and  hasattr(bd, '__dict__') :
            ads = ".".join(ad.__dict__.keys())
            bds = ".".join(bd.__dict__.keys())
            if not ads == bds :
                return False
            if checkfields == None :
                for k in ad.__dict__.iterkeys() :
                    if not ad.__dict__[k] == bd.__dict__[k] :
                        return False;
            else :
                for k in checkfields :
                    if not ad.__dict__[k] == bd.__dict__[k] :
                        return False;
            return True
        else :
            return False
    # --------------------------------------------------------------------------------
    now                      = dt.datetime.now()
    prefset = EmptyForm()
    pdict   = dict(MemberPreference.prefclasses)
    for c in pdict.iterkeys() :
        prefset.fields[c] = forms.BooleanField(required=False, label=pdict[c], help_text='Check the box to request this service.')
        if c in req.POST.keys() :
            if req.POST[c] == 'on' :
                prefset.fields[c].initial = True
        else :
            prefset.fields[c].initial = False
    
    formdict['address_form'] = MailAddressForm(req.POST)
    formdict['d_form']       = DuesForm(req.POST)
    formdict['email_form']   = EMailAddressForm(req.POST)
    formdict['form_error']   = ErrorList()
    formdict['j_form']       = JournalForm(req.POST)
    formdict['lookup']       = Lookup()
    formdict['member_form']  = MemberForm(req.POST)
    formdict['member_id']    = "new"
    formdict['p_form']       = PetForm(req.POST) 
    formdict['page_title']   = "Please Check This Entry"
    formdict['pref_flags']   = prefset
    formdict['telnum_form']  = TelNumberForm(req.POST)
    formdict['window_title'] = "Please Check this Entry" 
    
    # POST data from a form concerning what may be a new member.
    
    if  formdict['address_form'].is_valid() and \
        formdict['d_form'].is_valid()       and \
        formdict['email_form'].is_valid()   and \
        formdict['j_form'].is_valid()       and \
        formdict['member_form'].is_valid()  and \
        formdict['p_form'].is_valid()       and \
        formdict['telnum_form'].is_valid() :
        
        # Never-before-seen person joining?
        
        if not member_id :

            # Member's address: Street similar to that of an existing
            # MailAddress? (Housemates are often entered as pairs
            # (triplets, quadruplets...), and this may very well can
            # be the second (third, fourth...) of a pair (triplet,
            # quadruplet...)

            if hasattr(formdict['address_form'], 'cleaned_data') and formdict['address_form'].getStatusFlags() : 
                uspsaddrqset = MailAddress.objects.filter(
                                                           Q(street__icontains=formdict['address_form'].cleaned_data['street'])   &
                                                           Q(aptnum__icontains=formdict['address_form'].cleaned_data['aptnum'])   &
                                                           Q(zipcode__exact=formdict['address_form'].cleaned_data['zipcode'])
                                                         )
                if uspsaddrqset.count() > 0 :
                    # Got the US mail address from a housemate - use it instead of making a new address record.
                    madr = uspsaddrqset[0]
                else :
                    # Nothing seems to match, not doing fuzzy compares so we are not addressing 'close and possibly likely matches'.
                    madr = MailAddress (
                                         aptnum  = formdict['address_form'].cleaned_data['aptnum'],
                                         city    = formdict['address_form'].cleaned_data['city'],
                                         company = formdict['address_form'].cleaned_data['company'],
                                         country = 'US',
                                         state   = formdict['address_form'].cleaned_data['state'],
                                         street  = formdict['address_form'].cleaned_data['street'],
                                         zipcode = formdict['address_form'].cleaned_data['zipcode'],
                                         zipext  = formdict['address_form'].cleaned_data['zipext']
                                       )
                    madr.save()
            else :
                madr = None 
            # Member's email address
            if hasattr(formdict['email_form'], 'cleaned_data') : 
                try :
                    formdict['email_form'].clean()
                except forms.ValidationError :
                    pass
                emailqset =  EMailAddress.objects.filter(
                                                          Q(name__exact=formdict['email_form'].cleaned_data['em_name'])   &
                                                          Q(domain__exact=formdict['email_form'].cleaned_data['em_domain'])
                                                        )

                if emailqset.count() > 0 :
                    # Got a matching email address from a housemate - ditto as with mail address
                    emadr = emailqset[0]
                else :

                    emadr    = EMailAddress (
                                              name   = formdict['email_form'].cleaned_data['em_name'],  
                                              domain = formdict['email_form'].cleaned_data['em_domain']  
                                            )
                    emadr.save()
            else :
                emadr = None 

            # Member's telephone
            if hasattr(formdict['telnum_form'], 'cleaned_data') and not formdict['telnum_form'].getStatusFlags() : 

                telqset      =  TelNumber.objects.filter(
                                                          Q(area__exact=formdict['telnum_form'].cleaned_data['tf_area'])   &
                                                          Q(exch__exact=formdict['telnum_form'].cleaned_data['tf_exch'])   &
                                                          Q(number__exact=formdict['telnum_form'].cleaned_data['tf_line'])
                                                         )
                if telqset.count() > 0 :
                    # Got a matching telephone from a housemate - ditto as with mail address
                    telnum = telqset[0]
                elif isinstance(formdict['telnum_form'].cleaned_data['tf_ext'], decimal.Decimal) :
                    telnum   = TelNumber (
                                           area     = formdict['telnum_form'].cleaned_data['tf_area'],
                                           exch     = formdict['telnum_form'].cleaned_data['tf_exch'],
                                           number   = formdict['telnum_form'].cleaned_data['tf_line'],
                                           ext      = formdict['telnum_form'].cleaned_data['tf_ext']
                                         )
                    telnum.save()
                else :    
                    telnum   = TelNumber (
                                           area     = formdict['telnum_form'].cleaned_data['tf_area'],
                                           exch     = formdict['telnum_form'].cleaned_data['tf_exch'],
                                           number   = formdict['telnum_form'].cleaned_data['tf_line'],
                                           ext      = decimal.Decimal('0')
                                         )
                    telnum.save()
            else :
                telnum = None  

            # Got its parent objects (maybe); now set up the member record...
            
            mbr = Member(
                         mailadr   = madr,
                         emailadr  = emadr,
                         telnumber = telnum,
                         salute    = formdict['member_form'].cleaned_data['mf_salute'],
                         first     = formdict['member_form'].cleaned_data['mf_first'],
                         middle    = formdict['member_form'].cleaned_data['mf_middle'],
                         last      = formdict['member_form'].cleaned_data['mf_last'],
                         suffix    = formdict['member_form'].cleaned_data['mf_suffix']
                        )
            mbr.save()

            # Pets
            if  hasattr(formdict['p_form'], 'cleaned_data') and not (formdict['p_form'].getStatusFlags() & 6): 
                    
                first_pet = Pet (
                                  name        = formdict['p_form'].cleaned_data['pf_name'],
                                  description = formdict['p_form'].cleaned_data['pf_desc'],
                                )
                first_pet.save()
                pet_rel   = MemberPet(
                                       member = mbr,
                                       pet    = first_pet
                                     )
                pet_rel.save()
                
                if not(formdict['p_form'].getStatusFlags() & 1) and formdict['p_form'].cleaned_data['pf_dgtg'].isdigit() :
                    dog_tag_data = int(formdict['p_form'].cleaned_data['pf_dgtg'])
                    dog_tag      = DogTag(
                                           petid     = first_pet,
                                           tagnumber = dog_tag_data,
                                           issuedate = now,
                                           tagstatus = 'Assigned'
                                         )
                    dog_tag.save()
            else :
                first_pet = pet_rel = dog_tag = None

            # Member's initial Dues payment and corresponding journal
            # entry - default or entered: there needs to be a
            # corresponding journal entry!

            if  hasattr(formdict['d_form'], 'cleaned_data') and not formdict['d_form'].getStatusFlags(): 
                initpay = formdict['d_form'].cleaned_data['df_amount']

                if  hasattr(formdict['j_form'], 'cleaned_data') and not formdict['j_form'].getStatusFlags(): 
                    if formdict['j_form'].cleaned_data['jf_subject']  != None and len(formdict['j_form'].cleaned_data['jf_subject'])> 0 :
                        jentry = Journal (
                                            memberid  = mbr,
                                            entrydate = now,
                                            entrytype = formdict['j_form'].cleaned_data['jf_subject'],
                                            comment   = formdict['j_form'].cleaned_data['jf_comment']
                                         )
                        jentry.save()
                else :
                    # Compose a default journal entry comprised of bits from various member detail form entries.
                    first_comment = "%s joined on %s. Address: %s Email: %s Telephone: %s First dues payment: %s" % (unicode(mbr), unicode(now), unicode(madr), unicode(emadr), unicode(telnum), unicode(initpay))
                    if first_pet and pet_rel :
                        first_comment += " Pet: %s" % (first_pet.name)
                        if len(first_pet.description) :
                            first_comment += " Description: %s" % ( first_pet.description)
                        else :
                            first_comment += " No description given."
                    else :
                        first_comment += " No pets given."
                    
                    jentry = Journal (
                                        memberid  = mbr,
                                        entrydate = now,
                                        entrytype = 'Initial',
                                        comment   = first_comment
                                     )
                    jentry.save()

                dues     = Dues(
                                 memberid  = mbr,
                                 journalid = jentry,
                                 paydate   = now,
                                 payamount = initpay,
                                 paytype   = formdict['d_form'].cleaned_data['df_paytype']
                               )
                dues.save()

                # Member preferences

                pstring    = ""
                memberpref = MemberPreference()
                for c in pdict.iterkeys() :
                    if prefset.fields[c].initial == True :
                        pstring += "%s," % c
                memberpref.prefs    = pstring.rstrip(',')
                memberpref.memberid = mbr
                memberpref.save()

                # If this far, bless the transaction

                transaction.commit()
                return HttpResponseRedirect(reverse('fidoonline.membermanage.views.detailonemember', args=(mbr.memberid,)))
            else :
                formdict['form_error'] += ErrorList(['Expected an initial dues payment.'])
                return render_to_response('membermanage/formbase.html', formdict) 

        else : # Data change on existing member
            oldmailadr   = None
            oldemailadr  = None
            oldtelnumber = None
            oldmbr       = None 
            mbr          = Member.objects.get(pk=member_id)
            mbrupdate    = False
            formdict['member_id']    = member_id

            ### Mail Address Update ###
            cf =  formdict['address_form'].getStatusFlags()
            if hasattr(formdict['address_form'], 'cleaned_data') and cf == 31 :
                # Addresses are shared .
                oldmailadr = mbr.mailadr
                newmailadr = MailAddress()
                _updateformsec({'aptnum': 'aptnum', 'city': 'city', 'company':'company', 'state':'state', 'street':'street', 'zipcode':'zipcode', 'zipext':'zipext'}, newmailadr, formdict['address_form'])
                if not _dup(oldmailadr, newmailadr, checkfields=['aptnum', 'city', 'state', 'street', 'zipcode', 'zipext']) :
                    newmailadr.save()
                    mbr.mailadr = newmailadr
                    mailjournal = Journal(entrytype='Address', memberid=mbr, comment='Was %s' % (unicode(oldmailadr)))
                    mailjournal.save()
                    mbrupdate = True
                else :
                    oldmailadr = None
            elif hasattr(formdict['address_form'], 'cleaned_data') and cf == 0 :        
                # NO address whatsoever is replacing the old address. (We don't know where they live anymore). 
                # Check if old address is still being used before deleting.
                oldmailadr  = mbr.mailadr
                mbr.mailadr = None
                mbrupdate   = True
                
            ### EMail Address Update ###
            cf = formdict['email_form'].getStatusFlags()
            if hasattr(formdict['email_form'], 'cleaned_data') and not cf :
                oldemailadr = mbr.emailadr
                newemailadr = EMailAddress()
                _updateformsec({'name': 'em_name', 'domain': 'em_domain'}, newemailadr, formdict['email_form'])
                if not _dup(oldemailadr, newemailadr, checkfields=['name', 'domain']) :
                    newemailadr.save()
                    mbr.emailadr = newemailadr
                    emailjournal = Journal(entrytype='EMail', memberid=mbr, comment='Was %s' % (unicode(oldemailadr)))
                    emailjournal.save()
                    mbrupdate = True
                else :
                    oldemailadr = None
            elif hasattr(formdict['email_form'], 'cleaned_data') and not formdict['email_form'].getStatusFlags() :
                # NO email address whatsoever is replacing the old one. (We don't know their email anymore). 
                # Check if old email address is still being used before deleting.
                oldemailadr  = mbr.emailadr
                mbr.emailadr = None
                mbrupdate    = True
                
            ### Telephone Update ###
            cf = formdict['telnum_form'].getStatusFlags()
            if hasattr(formdict['telnum_form'], 'cleaned_data') and not cf :
                oldtelnumber = mbr.telnumber
                newtelnumber = TelNumber()
                _updateformsec({'area': 'tf_area', 'exch': 'tf_exch', 'number': 'tf_line', 'ext': 'tf_ext' }, newtelnumber, formdict['telnum_form'])
                if not _dup(oldtelnumber, newtelnumber, checkfields=['area', 'exch', 'number', 'ext']) :
                    try:
                        newtelnumber.area   = decimal.Decimal(newtelnumber.area)
                        newtelnumber.exch   = decimal.Decimal(newtelnumber.exch)
                        newtelnumber.number = decimal.Decimal(newtelnumber.number)
                        if hasattr(newtelnumber.ext, '__float__') :
                            newtelnumber.ext = decimal.Decimal(newtelnumber.ext)
                        elif hasattr(newtelnumber.ext, '__len__') and newtelnumber.ext.isdigit() :
                            newtelnumber.ext = decimal.Decimal(newtelnumber.ext)
                    except decimal.InvalidOperation :
                        newtelnumber = None
                    if newtelnumber != None :
                        newtelnumber.save()
                        mbr.telnumber = newtelnumber
                        telnumjournal = Journal(entrytype='Telephone', memberid=mbr, comment='Was %s' % (unicode(oldtelnumber)))
                        telnumjournal.save()
                        mbrupdate = True
                else :
                    oldtelnumber = None
            else :
                # NO phone number is displacing a current phone number (Number has changed - we don't know what the new number is). 
                oldtelnumber  = mbr.telnumber
                mbr.telnumber = None
                mbrupdate     = True
                
            ### Member Update ###
            if hasattr(formdict['member_form'], 'cleaned_data'):
                if mbr.salute != formdict['member_form'].cleaned_data['mf_salute'] or \
                   mbr.first  != formdict['member_form'].cleaned_data['mf_first']  or \
                   mbr.middle != formdict['member_form'].cleaned_data['mf_middle'] or \
                   mbr.last   != formdict['member_form'].cleaned_data['mf_last']   or \
                   mbr.suffix != formdict['member_form'].cleaned_data['mf_suffix'] :
                    _updateformsec({'salute': 'mf_salute', 'first': 'mf_first', 'middle': 'mf_middle', 'last': 'mf_last', 'suffix': 'mf_suffix' }, mbr, formdict['member_form'])
                    oldmbr = Member.objects.get(pk=member_id)
                    namejournal = Journal(entrytype='Identity', memberid=mbr, comment='Was %s' % (unicode(oldmbr)))
                    namejournal.save()
                    mbrupdate = True
            if mbrupdate :    
                mbr.save()

            ### Child record update - journal, pet, and dues ###    
            if hasattr(formdict['p_form'], 'cleaned_data') :
                if len(formdict['p_form'].cleaned_data['pf_name']) :
                    npet     = Pet(name = formdict['p_form'].cleaned_data['pf_name'], description = formdict['p_form'].cleaned_data['pf_desc'])
                    npet.save()
                    relation = MemberPet(member = mbr, pet = npet)
                    relation.save()
                    if len(formdict['p_form'].cleaned_data['pf_dgtg']) and formdict['p_form'].cleaned_data['pf_dgtg'].isdigit() :
                        dogtag = DogTag(petid = npet, tagnumber = int(formdict['p_form'].cleaned_data['pf_dgtg']), issuedate = now, tagstatus = 'Assigned')
                        dogtag.save()
                    petjournal = Journal(entrytype='Pet', memberid=mbr, comment='New pet %s' % (unicode(npet)))
                    petjournal.save()
            if hasattr(formdict['j_form'], 'cleaned_data') :
                if len(formdict['j_form'].cleaned_data['jf_subject']) and len(formdict['j_form'].cleaned_data['jf_comment']) : 
                    jentry = Journal()
                    _updateformsec({'entrytype':'jf_subject', 'comment': 'jf_comment'}, jentry, formdict['j_form'])
                    jentry.memberid = mbr
                    jentry.save()
                else :
                    jentry = None
            else :
                jentry = None
            ### Dues and Journal ###
            if hasattr(formdict['d_form'], 'cleaned_data') :
                ec = int(formdict['d_form'].cleaned_data['df_paytype'] == None)*2 + int(formdict['d_form'].cleaned_data['df_amount'] == None)
                if ec == 0 :
                    if jentry == None or jentry.entrytype != 'Payment' :
                        transaction.rollback()
                        raise forms.ValidationError ("Dues entry also requires a 'Payment' type journal entry (check amount, account, check number details or similar details.)")
                    duesentry = Dues()
                    _updateformsec({'payamount': 'df_amount', 'paytype': 'df_paytype'}, duesentry, formdict['d_form'])
                    duesentry.journalid = jentry
                    duesentry.memberid  = mbr
                    duesentry.save()

            # cleanup old parent records

            if oldmailadr   != None :
                # New address replacing old address. Check if old address is still being used before deleting.
                mqs = Member.objects.filter(mailadr__exact=oldmailadr)
                if mqs.count() == 0 :
                    # ref count on old mail address has gone to zero - delete it; no fido body lives there any more
                    oldmailadr.delete()
                    
            if oldemailadr  != None :
                mqs = Member.objects.filter(emailadr__exact=oldemailadr)
                if mqs.count() == 0 :
                    # ref count on old mail address has gone to zero - delete it; no fido body lives there any more
                    oldemailadr.delete()

            if oldtelnumber != None :
                mqs = Member.objects.filter(telnumber__exact=oldtelnumber)
                if mqs.count() == 0 :
                    # ref count on old telephone number is only self - delete it; no fido body uses it any more
                    oldtelnumber.delete()

            # If this far, bless the transaction
            transaction.commit()
            return HttpResponseRedirect(reverse('fidoonline.membermanage.views.detailonemember', args=(mbr.memberid,)))
    else : ### One or more form subsections are not valid.
        formdict['form_error'] += (
                                   formdict['address_form'].non_field_errors() +
                                   formdict['d_form'].non_field_errors()       +
                                   formdict['email_form'].non_field_errors()   +
                                   formdict['j_form'].non_field_errors()       +
                                   formdict['member_form'].non_field_errors()  +
                                   formdict['p_form'].non_field_errors()       + 
                                   formdict['telnum_form'].non_field_errors()
                                  ) 
        return render_to_response('membermanage/formbase.html', formdict) 
# -------------------------------------------------------------------------------------
def providememberdata (member_id, formdict) :
    """
    Furnish details for the member with the given ID.
    """
    import datetime as dt
    from django import forms
    member       = get_object_or_404(Member, pk=member_id)
    formdict['window_title'] = unicode(member)
    formdict['page_title']   = "Details for %s %s" % (member.first, member.last)
    formdict['member_id']    = member.memberid
    formdict['member_form']  = memberform = MemberForm()
    formdict['lookup'] = Lookup()
    memberform.fields['mf_salute'].initial = '%s' % (member.salute)
    memberform.fields['mf_first'].initial  = '%s' % (member.first)
    memberform.fields['mf_middle'].initial = '%s' % (member.middle) 
    memberform.fields['mf_last'].initial   = '%s' % (member.last) 
    memberform.fields['mf_suffix'].initial = '%s' % (member.suffix)
    if member.mailadr :
        formdict['address_form'] = MailAddressForm(instance=member.mailadr)
    else :
        formdict['address_form'] = MailAddressForm()
    if member.telnumber :
        formdict['telnum_form'] = telnum = TelNumberForm()
        telnum.fields['tf_area'].initial = '%03d' % (member.telnumber.area)
        telnum.fields['tf_exch'].initial = '%03d' % (member.telnumber.exch)
        telnum.fields['tf_line'].initial = '%04d' % (member.telnumber.number)
        if member.telnumber.ext != None :
            telnum.fields['tf_ext'].initial  = '%04d' % (member.telnumber.ext)
        else :
            telnum.fields['tf_ext'].initial  = ''
            
    else :
        formdict['telnum_form'] = TelNumberForm()
    if member.emailadr :
        formdict['email_form'] = emailadr = EMailAddressForm()
        emailadr.fields['em_name'].initial   = '%s' % (member.emailadr.name)
        emailadr.fields['em_domain'].initial = '%s' % (member.emailadr.domain)
    else :
        formdict['email_form'] = EMailAddressForm()
    # Journal
    formdict['j_entries'] = jset = []
    jqs = Journal.objects.filter(memberid__exact=member.memberid)
    for je in jqs :
        jset.append({'date': "%s" % (je.entrydate.strftime('%b %d %Y')), 'subject': "%s" % je.entrytype, 'detail': "%s" % (je.comment)})
    formdict['j_form'] = JournalForm()     
    # Dues
    formdict['d_entries'] = dset = []
    dqs = Dues.objects.filter(memberid__exact=member.memberid)
    for de in dqs :
        dset.append({'date': "%s" % (de.paydate.strftime('%b %d %Y')), 'type': "%s" % de.paytype, 'amount': "%s" % (de.payamount)})
    formdict['d_form'] = DuesForm()    
    # Dues Review
    now    = dt.datetime.now()
    expiry = member.term['expiry']
    formdict['r_entry'] = rset = {'htmlclass' : 'aok', 'entry' : ""}
    if   expiry <= 90 and expiry > 0 :
        rset['htmlclass'] = 'exn'
    elif expiry <= 0 and expiry > -90 :
        rset['htmlclass'] = 'exp'
    elif expiry <= -90 :
        rset['htmlclass'] = 'err'
    if expiry > 0 :
        rset['entry'] = "%d days until expiry, as of %s. Term ends %s." % (expiry, now.strftime('%b %d %Y'), member.term['end'].strftime('%b %d %Y'))
    elif expiry == 0 :
        rset['entry'] = "Expires today: %s" % (now.strftime('%b %d %Y'))
    else :    
        rset['entry'] = "%d days since expiry, as of %s. Term ended %s." % (-expiry, now.strftime('%b %d %Y'), member.term['end'].strftime('%b %d %Y'))
    # Pets
    formdict['p_entries'] = pset = []
    mpqs = MemberPet.objects.filter(member__exact=member.memberid)
    for pid in mpqs :
        cpet   = Pet.objects.get(pk=pid.pet.petid)
        dgtgqs = DogTag.objects.filter(petid__exact=cpet.petid)
        dtc = dgtgqs.count()
        dts = ""
        if dtc > 0:
            for kk in range(0, dtc) :
                dts = '%s%06d %s\n' % (dts, dgtgqs[kk].tagnumber, dgtgqs[kk].tagstatus)
        else :
            dts = 'None'
        pset.append({'identifier': cpet.petid, 'name': cpet.name, 'description' : cpet.description, 'dogtag' : dts})
    formdict['p_form'] = PetForm()    
    # Preferences
    pdict = dict(MemberPreference.prefclasses)
    formdict['pref_flags'] = prefset = EmptyForm()
    for c in pdict.iterkeys() :
        prefset.fields[c] = forms.BooleanField(required=False, label=pdict[c], help_text='Check the box to request this service.')
        prefset.fields[c].initial = False
    for pkey in MemberPreference.objects.get(pk=member.memberid).prefs.split(',') :
        prefset.fields[pkey].initial = True
