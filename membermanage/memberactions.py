"""
memberactions.py
HTTP request object processors for the membermanage application.
"""
from django                             import forms
from django.db                          import transaction
from django.core.context_processors     import csrf
from django.shortcuts                   import get_object_or_404, render_to_response
from django.http                        import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers           import reverse
from django.contrib.auth.decorators     import login_required
from django.forms.util                  import ErrorList
from fidoonline.membermanage.models     import DogTag, Dues, EMailAddress, Journal, MailAddress, Member, MemberPet, MemberPreference, Pet, TelNumber
from fidoonline.membermanage.forms      import DuesForm, EMailAddressForm, EmptyForm, JournalForm, Lookup, MailAddressForm, MemberForm, PetForm, TagForm, TelNumberForm
from fidoonline.membermanage.memberutil import find_member_submit, getstatusstyle, mkmembercontactdictionary, mkmemberdueslist, mkmemberpetlist, mkmemberpicker, mknonmemberpetlist, updateformsec, util_badtagonly, util_emptyform, util_registerpet, util_setmemberpreferences

# import pydb

# ---------------------------------------------------------------------------
@login_required
def requestchangename    (req, member_id) :
    """
    Request object is from the member detail page; the change member's name
    submit button was hit. Return a response and a context dictionary for either
    a membercontact template (the POST was intelligible) or a membernameupdate
    template (The POST was incomplete or not clean, so we ask for the name anew )
    """
    form = MemberForm(req.POST)
    if form.is_valid() :
        # (1) Complete & Valid form, (2) no member identifier = (3) New member
        if not member_id :
            member = Member(
                             mailadr   = None,
                             emailadr  = None,
                             telnumber = None,
                             salute    = form.cleaned_data['mf_salute'],
                             first     = form.cleaned_data['mf_first'],
                             middle    = form.cleaned_data['mf_middle'],
                             last      = form.cleaned_data['mf_last'],
                             suffix    = form.cleaned_data['mf_suffix']
                            )
            member.save()
            cntxdict = {}
            cntxdict.update(csrf(req))
            cntxdict.update({'member' : mkmembercontactdictionary(member)})
            return render_to_response('membermanage/membercontact.html', cntxdict)
        else :
            # (1) Complete & Valid form, (2) member identifier = (3) Name change of an existing member
            member =  Member.objects.get(pk=member_id)
            if req.POST.has_key('UpdateButton') :
                if hasattr(form, 'cleaned_data') :
                    if member.salute != form.cleaned_data['mf_salute'] or \
                       member.first  != form.cleaned_data['mf_first']  or \
                       member.middle != form.cleaned_data['mf_middle'] or \
                       member.last   != form.cleaned_data['mf_last']   or \
                       member.suffix != form.cleaned_data['mf_suffix'] :
                        updateformsec({'salute': 'mf_salute', 'first': 'mf_first', 'middle': 'mf_middle', 'last': 'mf_last', 'suffix': 'mf_suffix' }, member, form)
                        oldmbr = Member.objects.get(pk=member_id)
                        namejournal = Journal(entrytype='Identity', memberid=member, comment='Was %s' % (unicode(oldmbr)))
                        namejournal.save()
                        member.save()
            cntxdict = {}
            cntxdict.update(csrf(req))
            cntxdict.update({'member' : mkmembercontactdictionary(member)})
            return render_to_response('membermanage/membercontact.html', cntxdict)
    else :
        # (1) Incomplete or invalid form, (2) in any case repost the form
        mbr = Member.objects.get(pk=member_id)
        form = MemberForm()
        form.fields['mf_salute'].initial = '%s' % (mbr.salute)
        form.fields['mf_first'].initial  = '%s' % (mbr.first)
        form.fields['mf_middle'].initial = '%s' % (mbr.middle)
        form.fields['mf_last'].initial   = '%s' % (mbr.last)
        form.fields['mf_suffix'].initial = '%s' % (mbr.suffix)
        cntxdict = {}
        cntxdict.update(csrf(req))
        cntxdict.update({'member' : {'id' : member_id, 'form' : form}})
        return render_to_response('membermanage/membernameupdate.html', cntxdict)
# ---------------------------------------------------------------------------
@login_required
def requestchangeaddress (req, member_id) :
    """
    Request object is from the member detail page; the change member's ADDRESS
    submit button was hit. Return a response and a context dictionary for either
    a membercontact template (the POST was intelligible) or a response for the
    memberaddressupdate template (The POST was incomplete or not clean and we're
    asking for the address anew.)
    """

    def repost(member_id, form=None) :
        """
        Incomplete or invalid form: repost the form
        """
        mbr = Member.objects.get(pk=member_id)
        if not form :
            form  =  MailAddressForm()
            if mbr.mailadr != None :
                form.fields['street'].initial    = '%s' % (mbr.mailadr.street)
                form.fields['aptnum'].initial    = '%s' % (mbr.mailadr.aptnum)
                form.fields['city'].initial      = '%s' % (mbr.mailadr.city)
                form.fields['state'].initial     = '%s' % (mbr.mailadr.state)
                form.fields['zipcode'].initial   = '%s' % (mbr.mailadr.zipcode)
                form.fields['zipext'].initial    = '%s' % (mbr.mailadr.zipext)
        cntxdict = {}
        cntxdict.update(csrf(req))
        cntxdict.update({'member' : {'id' : member_id, 'form' : form}})
        return render_to_response('membermanage/memberaddressupdate.html', cntxdict)

    if req.POST.has_key('UpdateButton') :
        form  = MailAddressForm(req.POST)
        form.empty_permitted = True
        if form.is_valid() :
            # (1) Complete & Valid form, (2) no member identifier = (3)Error. Need a member first
            if not member_id :
                raise OperationalError("Asking for an address change on an unknown member - Create Member first")
                return None
            else :
                # (1) Complete & Valid form, (2) member identifier = (3) Address change of an existing member
                member =  Member.objects.get(pk=member_id)
                if hasattr(form, 'cleaned_data') :
                    if len(form.cleaned_data) == 0 :
                        if member.mailadr   != None :
                            mailjournal      = Journal(entrytype='Address', memberid = member, comment = 'Old Address was: %s. Current address not known.' % unicode(member.mailadr))
                            othermembersqset = Member.objects.filter(mailadr__exact=member.mailadr_id)
                            if othermembersqset.count() > 1 :
                                member.mailadr = None
                                member.save()
                            else :
                                oldmailadr     = MailAddress.objects.filter(adrid__exact=member.mailadr_id)
                                member.mailadr = None
                                member.save()
                                oldmailadr.delete()
                            mailjournal.save()
                    else :
                        mailadr = MailAddress()
                        mailadr.street  = form.cleaned_data.get('street')
                        mailadr.city    = form.cleaned_data.get('city')
                        mailadr.aptnum  = form.cleaned_data.get('aptnum')
                        mailadr.state   = form.cleaned_data.get('state')
                        mailadr.zipcode = form.cleaned_data.get('zipcode')
                        mailadr.zipext  = form.cleaned_data.get('zipext')
                        if member.mailadr == None :
                            mailjournal     = Journal(entrytype='Address', memberid=member, comment='New Address - No previous.')
                        else :
                            mailjournal     = Journal(entrytype='Address', memberid = member, comment = 'Old Address - %s.' % unicode(member.mailadr))
                        mailadr.save()
                        mailjournal.save()
                        oldmailadr = member.mailadr
                        member.mailadr = mailadr
                        member.save()
                        othermembersqset = Member.objects.filter(mailadr__exact=oldmailadr)
                        if othermembersqset.count() == 0 :
                            oldmailadr.delete()
                cntxdict = {}
                cntxdict.update(csrf(req))
                cntxdict.update({'member' : mkmembercontactdictionary(member)})
                return render_to_response('membermanage/membercontact.html', cntxdict)
        else :
            return repost(member_id, form)
    elif req.POST.has_key('ChangeMailButton') :
        return repost(member_id)
    else :
        return HttpResponseRedirect(reverse('fidoonline.membermanage.memberviews.detailmembercontact', args=[member_id]))
# ---------------------------------------------------------------------------
@login_required
def requestchangeemail   (req, member_id) :
    """
    Request object is from the member detail page; the change member's EMAIL ADDRESS
    submit button was hit. Return a response and a context dictionary for either
    a membercontact template (the POST was intelligible; confirm the entry) or a
    response for the memberemailaddressupdate template (The POST was incomplete
    or not clean and we're asking anew for the email address.)
    """
    def repost (member_id, form=None) :
        """
        Partially correct form, if furnished. Repost with existing
        content (and validator furnished error msgs) Otherwise,
        compose clean form and populate with database values, if
        available and blank otherwise.
        """
        mbr = Member.objects.get(pk=member_id)
        if not form :
            form  =  EMailAddressForm()
            if mbr.emailadr != None :
                form.fields['em_name'].initial    = '%s' % (mbr.emailadr.name)
                form.fields['em_domain'].initial  = '%s' % (mbr.emailadr.domain)
        cntxdict = {}
        cntxdict.update(csrf(req))
        cntxdict.update({'member' : {'id' : member_id, 'form' : form}})
        return render_to_response('membermanage/memberemailaddressupdate.html', cntxdict)

    if req.POST.has_key('UpdateButton') :
        form =  EMailAddressForm(req.POST)
        if form.is_valid() :
            # (1) Complete & Valid form, (2) no member identifier = (3)Error. Need a member first
            if not member_id :
                raise OperationalError("Asking for an email address change on an unknown member - Member should already exist")
                return None
            else :
                # (1) Complete & Valid form, (2) member identifier = (3) Email Address change of an existing member
                member =  Member.objects.get(pk=member_id)
                if hasattr(form, 'cleaned_data') :
                    emailadr        = EMailAddress()
                    emailadr.name   = form.cleaned_data.get('em_name')
                    emailadr.domain = form.cleaned_data.get('em_domain')
                    emailadr.save()
                    if member.emailadr == None :
                        emailjournal     = Journal(entrytype='EMail', memberid=member, comment='New Email Address - No previous one registered.')
                    else :
                        emailjournal     = Journal(entrytype='EMail', memberid=member, comment='Old Email Address - %s.' % unicode(member.emailadr))
                    emailjournal.save()
                    member.emailadr = emailadr
                    member.save()
                cntxdict = {}
                cntxdict.update(csrf(req))
                cntxdict.update({'member' : mkmembercontactdictionary(member)})
                return render_to_response('membermanage/membercontact.html', cntxdict)
        # (1) Incomplete or invalid form, (2) special case: blank email form means the old email doesn't work, but a new one is not known.
        elif form._errors.has_key('em_domain') and form._errors.has_key('em_name') :
            member  = Member.objects.get(pk=member_id)
            emailqs = Member.objects.filter(emailadr__exact=member.emailadr)
            if emailqs.count() :
                for member in emailqs :
                    emailjournal     = Journal(entrytype='EMail', memberid=member, comment='Email bounced - Was %s.' % (member.emailadr))
                    emailjournal.save()
                    member.emailadr = None
                    member.save()
                return HttpResponseRedirect(reverse('fidoonline.membermanage.memberviews.detailmembercontact', args=[member_id]))
            else :    
                return repost (member_id, form)
        else : 
            return repost (member_id, form)
    elif req.POST.has_key('ChangeEMailButton') :
        return repost (member_id)
    else :
        return HttpResponseRedirect(reverse('fidoonline.membermanage.memberviews.detailmembercontact', args=[member_id]))
# ---------------------------------------------------------------------------
@login_required
def requestchangephone   (req, member_id) :
    """
    Request object is from the member detail page; the change member's TELEPHONE
    submit button was hit. Return a response and a context dictionary for either
    a membercontact template (the POST was intelligible; confirm the entry) or a
    response for the membertelephoneupdate template (The POST was incomplete
    or not clean and we're asking anew for the telephone number.)
    """
    def repost(member_id, form=None) :
        """
        Partially correct form - repost with existing content (and validator furnished error msgs
        """
        mbr   = Member.objects.get(pk=member_id)
        if not form :
            form  =  TelNumberForm()
            if mbr.telnumber != None :
                form.fields['tf_area'].initial   = '%s' % (mbr.telnumber.area)
                form.fields['tf_exch'].initial   = '%s' % (mbr.telnumber.exch)
                form.fields['tf_line'].initial   = '%s' % (mbr.telnumber.number)
                form.fields['tf_ext'].initial    = '%s' % (mbr.telnumber.ext)
        wmsg     = " - ".join(form.non_field_errors())
        cntxdict = {}
        cntxdict.update(csrf(req))
        cntxdict.update({'member' : {'id' : member_id, 'form' : form}, 'warningmsg': wmsg })
        return render_to_response('membermanage/membertelephoneupdate.html', cntxdict)

    def numbercheckandswitch(member, telnumber) :
        oldtel           = member.telnumber
        if telnumber == None or (hasattr(telnumber, 'isempty') and telnumber.isempty()) :
            member.telnumber = None
        else :    
            telnumber.save()
            member.telnumber = telnumber
        if oldtel :    
            teljournal       = Journal(entrytype='Telephone', memberid=member, comment='Old Telephone was %s.' % (str(oldtel)))
            # Are there others for whom
            # the old telephone record needs
            # to be preserved?
            telnumqs         = Member.objects.filter(telnumber__exact=oldtel)
            if telnumqs.count() == 0 :
                # Tis the only member who had this now
                # defunct number - it is safe to
                # delete it.
                oldtel.delete()
        else :
            if member.telnumber :
                teljournal       = Journal(entrytype='Telephone', memberid=member, comment='New Telephone - No previous one registered.')
            else : # member had no phone and was not given a phone. NOOP!
                teljournal       = None
        if not telnumber.isempty() and teljournal:
            teljournal.save()
            member.save()

    if req.POST.has_key('UpdateButton') :
        form = TelNumberForm(req.POST)
        if form.is_valid() :
            # (1) Complete & Valid form, (2) no member identifier = (3)Error. Need a member first
            if not member_id :
                raise OperationalError("Asking for a telephone number on an unknown member - Member should already exist")
                return None
            else :
                # (1) Complete & Valid form, (2) member identifier = (3) Telephone number change of an existing member
                member =  Member.objects.get(pk=member_id)
                if hasattr(form, 'cleaned_data') :
                    telnumber        = TelNumber()
                    telnumber.area   = form.cleaned_data.get('tf_area')
                    telnumber.exch   = form.cleaned_data.get('tf_exch')
                    telnumber.number = form.cleaned_data.get('tf_line')
                    telnumber.ext    = form.cleaned_data.get('tf_ext')
                    numbercheckandswitch(member, telnumber)
                cntxdict = {}
                cntxdict.update(csrf(req))
                cntxdict.update({'member' : mkmembercontactdictionary(member)})
                return render_to_response('membermanage/membercontact.html', cntxdict)
        else :
            # (1) Incomplete or invalid form, (2) in any case repost the form
            return repost(member_id, form)
    elif req.POST.has_key('ChangePhoneButton') :
        return repost(member_id)
    else :
        return HttpResponseRedirect(reverse('fidoonline.membermanage.memberviews.detailmembercontact',     args=[member_id]))
# ---------------------------------------------------------------------------
@login_required
def recordduespayment(req, member_id) :
    """
    Request object initially is from Dues Review table generated by
    fidoonline.membermanage.detailmemberdues. Make a form soliciting a
    new dues payment; In addition to creating a dues object, solicit a
    journal entry of type 'Payment' to capture the form of the
    payment: cash, check (with financial addenda), wampum beads, dog
    biscuits...
    """
    ptype = lambda member : {'ina': 'Reinstate', 'exp': 'Renew', 'exn': 'Renew', 'act': 'Renew', 'inf': 'New', 'inc': 'New'}[getstatusstyle(member)]
    if req.POST.has_key('CancelButton') or req.POST.has_key('UpdateButton') :
        dform = DuesForm(req.POST)
        jform = JournalForm(req.POST)
        if dform.is_valid() and jform.is_valid() :
            # (1) Complete & Valid forms, (2) no member identifier = (3)Error. Need a member first
            if not member_id :
                raise OperationalError("Posting dues and related journal entry on an unknown member - Member should already exist.")
                return None
            else :
                # (1) Complete & Valid form, (2) member identifier = (3) Dues and related Journal posting of an existing member
                member =  Member.objects.get(pk=member_id)
                if req.POST.has_key('UpdateButton') :
                    if hasattr(dform, 'cleaned_data') and hasattr(jform, 'cleaned_data') :
                        dp           = Dues()
                        jp           = Journal()
                        dp.memberid  = member
                        dp.paytype   = ptype(member)
                        dp.payamount = dform.cleaned_data.get('df_amount')
                        jp.memberid  = member
                        jp.entrytype = 'Payment'
                        jp.comment   = jform.cleaned_data.get('jf_comment')
                        jp.save()
                        dp.journalid = jp
                        dp.save()
                return  HttpResponseRedirect( reverse('fidoonline.membermanage.memberviews.detailmemberframeset', args=[member_id]))
        else :
            return  HttpResponseRedirect( reverse('fidoonline.membermanage.memberviews.detailmemberframeset', args=[member_id]))
##             try :
##                 member       = Member.objects.get(pk=member_id)
##                 membername   = ' '.join(str(member).split()[1:])
##             except Member.DoesNotExist :
##                 membername   = ''
##             if req.POST.has_key('UpdateButton') :
##                 bannerflag   = False;
##                 detailagents = {
##                                  'northwestsloturl' : reverse('fidoonline.membermanage.memberviews.detailmembercontact',     args=[member_id]),
##                                  'northeastsloturl' : reverse('fidoonline.membermanage.memberactions.recordduespayment',     args=[member_id]),
##                                  'southwestsloturl' : reverse('fidoonline.membermanage.memberviews.detailmemberpets',        args=[member_id]),       
##                                  'southeastsloturl' : reverse('fidoonline.membermanage.memberviews.detailmemberjournal',     args=[member_id]),
##                                  'southsloturl'     : reverse('fidoonline.membermanage.memberviews.detailmemberpreferences', args=[member_id]),  
##                                  'searchsloturl'    : reverse('fidoonline.membermanage.memberviews.findmemberbyname',        args=[bannerflag])  
##                                }
##                 slotdict = {
##                              'crumbline' : ({'label': 'Start Here', 'link': reverse('fidoonline.membermanage.starthereview.start')}, {'label': 'Member Directory', 'link': reverse('fidoonline.membermanage.views.memberlist')}, {'label': membername, 'link': None}),
##                              'slots'     : detailagents 
##                            }
##                 return render_to_response('membermanage/fivepanelframe.html', slotdict)
##             else :
##                 # Partially filled out form is irrelevant: user is cancelling instead.
##                 cntxdict = {}
##                 cntxdict.update(csrf(req))
##                 cntxdict.update({'member' : mkmemberdueslist(member, reverse('fidoonline.membermanage.memberactions.recordduespayment', args=[member_id]))})
##                 return  HttpResponseRedirect( reverse('fidoonline.membermanage.memberviews.detailmemberframeset', args=[member_id]))
    else :
        # No post - start of data entry dialog. Send fresh and empty forms.
        member =  Member.objects.get(pk=member_id)
        jform  = JournalForm()
        dform  = DuesForm()
        jform.fields['jf_subject'].initial = 'Payment'
        jform.fields['jf_comment'].initial = ''
        dform.fields['df_paytype'].initial = ptype(member)
        dform.fields['df_amount'].initial  = 0
        cntxdict = {}
        cntxdict.update(csrf(req))
        cntxdict.update({'member' : {'id' : member_id, 'dform' : dform, 'jform': jform}})
        return render_to_response('membermanage/memberduesadd.html', cntxdict)
# ---------------------------------------------------------------------------
@login_required
def recordpet(req, member_id) :
    """
    Register a new pet and, possibly, an associated tag. Establish co-ownership
    of a list of pets with another member.
    """
    import re

    # -----------------------------------------------------------------------
    def emptyform  (req, member_id, pform, tform) :
        """
        Pform is not valid, so the tag validity is irrelevant. Repost what
        seems to be clean and solicit the remainder.
        """
        cntxdict = {}
        cntxdict.update(csrf(req))
        cntxdict.update({'member' : {'id' : member_id, 'pform' : pform, 'tform': tform}})
        return render_to_response('membermanage/memberpetadd.html', cntxdict)
    # -----------------------------------------------------------------------
    def badtagonly  (req, member_id, pform, tform) :
        """
        No tform (tag not given or bogus). Accept unassigned case where the ta_mumber
        field in the raw POST is present but empty. Otherwise, sent form back to the client.
        """
        if req.POST.has_key('ta_number') and len(req.POST['ta_number']) == 0 :
            member, newpet, newtag, newlink = util_badtagonly(req, member_id, pform, tform)
            cntxdict = {}
            cntxdict.update(csrf(req))
            cntxdict.update({'member' : mkmemberpetlist(member, reverse('fidoonline.membermanage.memberactions.recordpet', args=[member_id]))})
            return render_to_response('membermanage/membertable.html', cntxdict)
        else :
            return emptyform(req, member_id, pform, tform)
    # -----------------------------------------------------------------------
    def registerpet (req, member_id, pform, tform) :
        """
        Pform and tform are valid: relate pet to member and tag to pet.
        """
        member, newpet, newtag, newlink = util_registerpet(req, member_id, pform, tform)
        cntxdict = {}
        cntxdict.update(csrf(req))
        cntxdict.update({'member' : mkmemberpetlist(member, reverse('fidoonline.membermanage.memberactions.recordpet', args=[member_id]))})
        return render_to_response('membermanage/membertable.html', cntxdict)
    # -----------------------------------------------------------------------
    def postshare (req, member_id) :
        """
        Repost the member search table with a petlist and a member picker
        so browser users might select co-owning members of a set of pets.
        """
        member   = Member.objects.get(pk=member_id)
        cntxdict = csrf(req)
        petdict  = mkmemberpetlist(member, reverse('fidoonline.membermanage.memberactions.recordpet', args=[member_id]))
        petdict.update({'addenda' : mkmemberpicker(req, reverse('fidoonline.membermanage.memberactions.recordpet', args=[member_id]), '_self')})
        cntxdict.update({'member' : petdict})
        return render_to_response('membermanage/membertable.html', cntxdict)
    # -----------------------------------------------------------------------
    def mpick (req, member_id, other_id=None) :
        """
        A member (other_id) has been designated as a co-owner of a
        member's pet (member_id). Create MemberPet records outside the
        intersection of already co-owned pets (between member_id and
        other_id, if any) to reflect the shared ownership. Create an
        HTTP response to reinstate the detail member pet's
        display. If, in the absence of other_id, then query the lookup text
        box for a constraining pattern and repost the (presumably
        reduced-size) member pick directory (done in postshare(), above).
        """
        if other_id :
            # The browser user has indicated that another member (other_id) 
            # shares pets owned by member_id. Should not create pairing
            # records where they already exist: only need records for pets
            # owned by member_id but not also already owned by other_id
            # (pets owned by member_id outside the intersection of pets
            # already owned both by member_id and other_id).  
            mset = set()
            oset = set()
            for pair in MemberPet.objects.filter(member__exact=member_id) :
                mset.add(pair.pet_id)
            for pair in MemberPet.objects.filter(member__exact=other_id) :
                oset.add(pair.pet_id)
            # uset: pets owned by member_id, but not (currently)
            # shared by other_id. Create new MemberPet pairing
            # records to reflect that the canines in uset are now also
            # shared between member_id and other_id
            uset = mset.difference(mset.intersection(oset))    
            if len(uset) > 0 :
                for pid in list(uset) :
                    nmp  = MemberPet()
                    nmp.member = Member.objects.get(pk=other_id)
                    nmp.pet    = Pet.objects.get(pk=pid)
                    nmp.save()
            # Send a 301 redirect to induce the user's browser to fetch a revised page.        
            return HttpResponseRedirect(reverse('fidoonline.membermanage.memberviews.detailmemberpets', args=[member_id]))
        else :
            # If the caller hasn't passed in another member's id (other_id == None) then
            # invoke postshare to resend the current page, but with additional member filtering that may have been
            # furnished by the user.
            return postshare(req, member_id)
    # -----------------------------------------------------------------------
    if req.POST.has_key('UpdateButton') :
        pform = PetForm(req.POST)
        tform = TagForm(req.POST)
        return [emptyform, emptyform, badtagonly, registerpet][int(pform.is_valid())*2 + int(tform.is_valid())](req, member_id, pform, tform)
    elif req.POST.has_key('CancelButton') :
        member      = Member.objects.get(pk=member_id)
        cntxdict = {}
        cntxdict.update(csrf(req))
        cntxdict.update( {'member' : mkmemberpetlist(member, reverse('fidoonline.membermanage.memberactions.recordpet', args=[member_id]))})
        return render_to_response('membermanage/membertable.html', cntxdict)
    elif req.POST.has_key('AddPetButton') :
        pform = PetForm()
        tform = TagForm()
        return emptyform(req, member_id, pform, tform)
    elif req.POST.has_key('SharePetButton') :
        return postshare(req, member_id)
    else: # Any key correspond to the pick of a sharing member?
        other_member_id = find_member_submit(req)
        if other_member_id :
            return mpick(req, member_id, other_member_id)
        else : # No, but mpick may need to restrict choices on a further constrained search string
            return mpick(req, member_id)
# ---------------------------------------------------------------------------
@login_required
def changepet(req, member_id, pet_id) :
    """
    This action handler supports operations on existing pets: name and description
    changes, tag assignments, co-owner associations and - grimly - dog deletions.
    """
    import re
    # -----------------------------------------------------------------------
    def mkeditcoownlist(coownQueryset) :
        """
        """
        rowset = []
        if coownQueryset.count() == 0 :
            rowset.append([{'data' : {'checkvalue': 'No FIDO dog tags have been assigned.'}, 'helptext': 'Hit \'Add/Reassign Tag\' to assign the first tag to this pet.', 'span' : 4}])
        else :
            indx = 1
            for coown in coownQueryset :
                chkdict = {'checkname' : 'COW-%05d' % (coown.member.memberid), 'checkvalue' : '%d' % (indx)}
                rowset.append([    \
                                {'data': {'checkvalue' : unicode('%05d' % coown.member.memberid)}, 'helptext' : 'Co-owner Membership ID', 'span' : 1},   \
                                {'data': {'checkvalue' : unicode('%s %s' % (coown.member.first, coown.member.last))}, 'helptext' : 'Pet Co-owner', 'span': 1},   \
                                {'data': chkdict, 'helptext' : 'Check this box to discontinue the co-owner relationship with %s %s.' % (coown.member.first, coown.member.last), 'span' : 1}  \
                              ])
                indx += 1
        return rowset

    # -----------------------------------------------------------------------
    def mkeditdogtaglist(dogtagQueryset) :
        """
        """
        import datetime as dt

        rowset = []
        if dogtagQueryset.count() == 0 :
            rowset.append([{'data' : {'checkvalue': 'No FIDO dog tags have been assigned.'}, 'helptext': 'Hit \'Add/Reassign Tag\' to assign the first tag to this pet.', 'span' : 4}])
        else :
            for dogtg in dogtagQueryset :
                chkdict = {'checkname' : 'TAG-%06d' % (dogtg.tagnumber), 'checkvalue' : '%s-%06d' % (dogtg.tagstatus, dogtg.tagnumber)}
                rowset.append([    \
                                {'data': {'checkvalue' : unicode('%06d' % dogtg.tagnumber)}, 'helptext' : 'Tag number as stamped on the dog tag.', 'span' : 1},   \
                                {'data': {'checkvalue' : unicode(dogtg.issuedate.strftime('%b %d, %Y'))}, 'helptext' : 'Day when tag assignment was recorded in the database', 'span': 1},   \
                                {'data': {'checkvalue' : dogtg.tagstatus}, 'helptext' : 'Tag ASSIGNED or LOST?', 'span' : 1},   \
                                {'data': chkdict, 'helptext' : 'Check this box if the tag has been RETURNED TO FIDO AND NO LONGER IS WITH THE DOG.', 'span' : 1}  \
                              ])
        return rowset
    # -----------------------------------------------------------------------
    tagre       = re.compile(r'^TAG-(?P<id>\d+)')
    coore       = re.compile(r'^COW-(?P<id>\d+)')
    mfunc       = lambda k : tagre.match(k)
    cfunc       = lambda k : coore.match(k)

    # On an update, the user has committed to various changes
    # concerning data about pets; particulars noted below.
    if req.POST.has_key('UpdateButton') :
        pform    = PetForm(req.POST)
        tform    = TagForm(req.POST)
        pcx      = tcx = False
        response = HttpResponseRedirect(reverse('fidoonline.membermanage.memberviews.detailmemberpets', args=[member_id]))

        # Changes to the dog's name or description are dealt with in
        # this corner.
        if pform.is_valid() :
            pet    =  get_object_or_404(Pet,    pk=pet_id)
            if pform.cleaned_data.has_key('pf_name') and len(pform.cleaned_data['pf_name']) > 0 :
                pet.name        = pform.cleaned_data.get('pf_name')
                pcx             = True;
            if pform.cleaned_data.has_key('pf_desc') and len(pform.cleaned_data['pf_desc']) > 0 :
                pet.description = pform.cleaned_data.get('pf_desc')
                pcx             = True;

        # Empty form elements (lack of a name or description) wind up
        # here. We re-submit the form; the validator has already
        # inserted error messages in the field, our lot is simply to
        # repost the form.
        else :
            pet    =  get_object_or_404(Pet,    pk=pet_id)
            member =  get_object_or_404(Member, pk=member_id)
            rdict  = {
                      'member'       : member,
                      'pet'          : pet,
                      'pform'        : pform,
                      'taglist'      : mkeditdogtaglist(DogTag.objects.filter(petid__exact=pet_id)),
                      'tform'        : tform
                     }
            rdict.update(csrf(req))
            response = render_to_response('membermanage/memberpetchange.html', rdict)

        # Tag numbers go to dogs without tags, unless an
        # already-tagged dog has lost one. The validator helpfully
        # checks if a dog has a tag or if the new tag is already
        # assigned (evidence of a prior screw-up). These cases are
        # marked invalid and are dealt with below. Validity means the
        # dog doesn't have a tag AND the entered tag number belongs to
        # no other dog. We record the new assignment and reset the
        # member's pet listing.

        if tform.is_valid() :
            tag                 = DogTag()
            tag.tagnumber       = tform.cleaned_data.get('ta_number')
            tag.tagstatus       = unicode('Assigned')
            tag.petid           = pet
            tcx                 = True
        else :
            # If validation discovered that the entered tag is already
            # in the database, must return thr form with a warning
            # (which is already in the form's non-field error list)
            member              = get_object_or_404(Member, pk=member_id)
            if req.POST.has_key('ta_number') and len(req.POST['ta_number']) > 0 :
                rdict  = {
                           'member'       : member,
                           'pet'          : pet,
                           'pform'        : pform,
                           'taglist'      : mkeditdogtaglist(DogTag.objects.filter(petid__exact=pet_id)),
                           'tform'        : tform
                         }
                rdict.update(csrf(req))
                response = render_to_response('membermanage/memberpetchange.html', rdict)
        if pcx  :
            pet.save()
        if tcx  :
            # If another tag is being posted, any current tag assigned
            # to the pet is, by definition, lost (rule: only one
            # assigned tag per dog at any given moment). Cycle through
            # current associated tags and marked them as 'Lost'.
            tqs       = DogTag.objects.filter(petid__exact=pet_id)
            if tqs.count() > 0 :
                for losttag in tqs :
                    losttag.tagstatus = 'Lost'
                    losttag.save()
            tag.save()

        # Users release tags here; 'Release' means that the physical
        # tag has been returned to FIDO and is no longer associated
        # with the dog. Lost tags should NOT be disassociated from the
        # dog. One never knows if an owner might find a tag and put it
        # on the pet again. To allow for this, we still keep lost tags
        # associated with the dogs they once were on and just mark
        # them as lost.
        releasetags = filter(mfunc, req.POST.keys())
        if len(releasetags) > 0 :
            for str in releasetags :
                mo = tagre.match(str)
                id = unicode(int(mo.groupdict()['id']))
                try :
                    tg = DogTag.objects.get(pk=id)
                except DogTag.DoesNotExist :
                    continue
                tg.delete()

        # Co-ownership disassociations happen here: the user ticks off
        # the name of any listed co-owner to dissassociate that member
        # with the dog; nothing much is lost: the member-pet pair
        # documenting the association is the only deletion that takes
        # place. RULE: If A and B own a dog and B wishes to relinquish
        # co-ownership, perform the edit from A's detail page, not
        # B's. By checking off B's name on A's page, B is cut loose
        # and A retains ownership of the dog.

        cobreaks = filter(cfunc, req.POST.keys())
        if len(cobreaks) > 0 :
            for coid in cobreaks :
                mo   = coore.match(coid)
                id   = unicode(int(mo.groupdict()['id']))
                mpqs = MemberPet.objects.filter(member__exact=id)
                if mpqs.count() > 0 :
                    for mprel in mpqs :
                        if mprel.pet.petid == int(pet_id) :
                            mprel.delete()
                            break
        return response

    # The big red delete button has been hit; client-side scripts have
    # already cautioned the user; this is for real. Django maintains
    # its own notion of 'foreign key' and, with the pet deleted,
    # related objects such as Member-Pet relations and Tag ownership
    # goes too. TODO: tags on dead dogs are nominally 'released' but,
    # to date, have not been returned to FIDO; really they are lost,
    # but not associated with dogs. Set up a new tag state to reflect:
    # 'buried with a dead dog.'

    if req.POST.has_key('DeleteButton') :
        # Nuke the pet
        pet    =  get_object_or_404(Pet,    pk=pet_id)
        pet.delete()
        return HttpResponseRedirect(reverse('fidoonline.membermanage.memberviews.detailmemberpets', args=[member_id]))

    # The user has abandoned whatever may have been entered in the forms.
    if req.POST.has_key('CancelButton') :
        # Null operation
        return HttpResponseRedirect(reverse('fidoonline.membermanage.memberviews.detailmemberpets', args=[member_id]))

    # 'Edit' button on membertable table display of pets has just been
    # hit; no pet edit form has been posted yet.

    if req.POST.has_key('ChangePetButton') :
        member =  get_object_or_404(Member, pk=member_id)
        pet    =  get_object_or_404(Pet,    pk=pet_id)
        pform  = PetForm()
        tform  = TagForm()
        pform.fields['pf_name'].initial = pet.name
        pform.fields['pf_desc'].initial = pet.description
        tform.fields['ta_number'].help_text = unicode('Enter the FIDO dog tag number stamped on the tag. If there is an ASSIGNED tag in the \'Associated FIDO Dog Tag\' list, THAT tag will be given a status of  \'Lost\' and THIS tag will become the assigned tag.')
        rdict  = {
                   'member'       : member,
                   'pet'          : pet,
                   'pform'        : pform,
                   'taglist'      : mkeditdogtaglist(DogTag.objects.filter(petid__exact=pet_id)),
                   'coownlist'    : mkeditcoownlist(MemberPet.objects.filter(pet__exact=pet_id)),
                   'tform'        : tform
                 }
        rdict.update(csrf(req))
        return render_to_response('membermanage/memberpetchange.html', rdict)
# ---------------------------------------------------------------------------
@login_required
def addjournalrecord(req, member_id) :
    """
    Add Correspondence or Remark Journal Entry
    """

    # -----------------------------------------------------------------------
    def nojournaladd(req, member_id) :
        """
        Journal entry abandoned by user
        """
        return HttpResponseRedirect(reverse('fidoonline.membermanage.memberviews.detailmemberjournal', args=[member_id]))

    # -----------------------------------------------------------------------
    def journaladd(req, member_id) :
        """
        """
        import datetime as dt

        form  = JournalForm(req.POST)
        if form.is_valid() :
            if not member_id :
                raise OperationalError("Posting a journal entry on an unknown member - Member should already exist.")
            else :
                member       = get_object_or_404(Member, pk=member_id)
                je           = Journal()
                je.entrytype = form.cleaned_data.get('jf_subject')
                je.comment   = form.cleaned_data.get('jf_comment')
                je.entrydate = dt.datetime.now()
                je.memberid  = member
                je.save()
                return HttpResponseRedirect(reverse('fidoonline.membermanage.memberviews.detailmemberjournal', args=[member_id]))
        else :
            member = get_object_or_404(Member, pk=member_id)
            rdict  = {
                       'member' : member,
                       'jform'  : form
                     }
            rdict.update(csrf(req))
            return render_to_response('membermanage/memberjournalentry.html', rdict)
    # -----------------------------------------------------------------------
    if req.POST.has_key('CancelButton')  : return nojournaladd(req, member_id)
    if req.POST.has_key('UpdateButton')  : return journaladd(req, member_id)
    if req.POST.has_key('JournalButton') :
        member = get_object_or_404(Member, pk=member_id)
        form   = JournalForm()
        rdict  = {
                   'member' : member,
                   'jform'  : form
                 }
        rdict.update(csrf(req))
        return render_to_response('membermanage/memberjournalentry.html', rdict)
# -----------------------------------------------------------------------
@login_required 
def setmemberpreferences(req, member_id) :
    """
    Preferences are presently binary flags that turn on/off a fixed (at the
    db level) number of standard preferences. As of 08-Feb-2011 this fixed
    list of preferences has two elements: 1. Getting the newsletter via U. S.
    mail and 2. Getting the broadcast email. 
    """
    member, memberpref =  util_setmemberpreferences(req, member_id)
    return HttpResponseRedirect(reverse('fidoonline.membermanage.memberviews.detailmemberpreferences', args=[member_id]))
