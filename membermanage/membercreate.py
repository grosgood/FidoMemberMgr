"""
membercreate.py
HTTP Request processors that manage the phases of creating
a new member record, then the adding of successive detail, to wit:
(1) U. S. mail
(2) electronic mail
(3) phone
(4) initial payment
(5) initial preferences 
(6) pet(s...) (a cycle of steps, as needed, one for each pet)
(7) optionally, create a new member record based largely on a pre-existing record
This is a wizard use case: where, in at least six steps, the wizard walks the
web user through the steps of creating a new, complete FIDO member record.
"""
from django.contrib.auth.decorators     import login_required
from django.core.context_processors     import csrf
from django.core.urlresolvers           import reverse
from django.http                        import HttpResponseRedirect, HttpResponseNotFound, HttpResponse
from django.shortcuts                   import render_to_response, get_object_or_404
from fidoonline.membermanage.memberutil import find_member_submit, getstatusstyle, mkjournallist, mkmembercontactdictionary, mkmemberdueslist, mkmemberpetlist, mkmemberpicker, mkmemberpreferences, mknonmemberdictionary, mknonmemberdueslist, mknonmemberjournallist, mknonmemberpetlist, mknonmemberpreferences, util_badtagonly, util_emptyform, util_registerpet, util_setmemberpreferences 
from fidoonline.membermanage.forms      import DuesForm, EMailAddressForm, EmptyForm, JournalForm, Lookup, MailAddressForm, MemberForm, PetForm, TagForm, TelNumberForm
from fidoonline.membermanage.models     import DogTag, Dues, EMailAddress, Journal, MailAddress, Member, MemberPet, MemberPreference, Pet, TelNumber
# import pydb

def mkmsg(title, message, fcolor="#fef0d0", bcolor="#100070") :
    return '<html><head><title>%s</title></head><body style="color:%s;background:%s;font-family:sans;font-size:large;font-weight:bold"><p>%s</p></body><html>' % (title, fcolor, bcolor, message)

# -------------------------------------------------------------------------------------
def makenewrecord(req):
    """
    detail/new/name
    """
    form = MemberForm(req.POST)
    if req.POST.has_key('AddNewMemberButton') and form.is_valid()  :
        # Create the member
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
        member_id = str(member.memberid)
        form = MailAddressForm()
        form.fields['street'].initial    = ''
        form.fields['city'].initial      = ''
        form.fields['state'].initial     = ''
        form.fields['zipcode'].initial   = ''
        form.fields['zipext'].initial    = ''
        cntxdict  = csrf(req)
        newmdict  = {'id' : member_id, 'form' : form, 'wizard': reverse('fidoonline.membermanage.membercreate.addaddress', args=[member_id])}
        newmdict['canurl'] = reverse('fidoonline.membermanage.memberviews.detailmemberframeset', args=[member_id])  
        cntxdict.update({'member' : newmdict, 'scriptlist': ['/sitemedia/js/fidositecore.js']})
        return render_to_response('membermanage/memberaddressupdate.html', cntxdict)
    else :
        member_id = '00000'
        cntxdict = csrf(req)
        cntxdict.update({'member' : {'id' : member_id, 'form' : form, 'wizard': reverse('fidoonline.membermanage.membercreate.makenewrecord')}, 'scriptlist': ['/sitemedia/js/fidositecore.js']})
        return render_to_response('membermanage/membernameupdate.html', cntxdict)

# -------------------------------------------------------------------------------------
@login_required
def addaddress(req, member_id) :
    """
    detail/new/address/(?P<member_id>\d+)
    """
    form = MailAddressForm(req.POST)
    if req.POST.has_key('AddAddressButton') and form.is_valid()  :
        # Add an address record to the member record. 
        if not member_id :
            raise OperationalError("Asking for an address change on an unknown member - Create Member first")
        try :
            member =  Member.objects.get(pk=member_id)
        except Member.DoesNotExist :
            return HttpResponseNotFound(content="There is no record for Member ID %s" % (member_id))
        if hasattr(form, 'cleaned_data') :
            mailadr = MailAddress()
            mailadr.aptnum   = form.cleaned_data.get('aptnum')
            mailadr.street   = form.cleaned_data.get('street')
            mailadr.city     = form.cleaned_data.get('city')
            mailadr.state    = form.cleaned_data.get('state')
            mailadr.zipcode  = form.cleaned_data.get('zipcode')
            mailadr.zipext   = form.cleaned_data.get('zipext')
            othermembersqset = Member.objects.filter(mailadr__street__exact=mailadr.street).filter(mailadr__aptnum__exact=mailadr.aptnum).filter(mailadr__city__exact=mailadr.city).filter(mailadr__state__exact=mailadr.state).filter(mailadr__zipcode__exact=mailadr.zipcode)
            if othermembersqset.count() == 0 :
                mailadr.save()
            else :
                mailadr = othermembersqset[0].mailadr
            member.mailadr = mailadr
            member.save()
            form  =  EMailAddressForm()
            form.fields['em_name'].initial    = ''
            form.fields['em_domain'].initial  = ''
            cntxdict  = csrf(req)
            newmdict  = {'id' : member_id, 'form' : form, 'wizard': reverse('fidoonline.membermanage.membercreate.addemail', args=[member_id])}
            newmdict['canurl'] = reverse('fidoonline.membermanage.memberviews.detailmemberframeset', args=[member_id])  
            cntxdict.update({'member' : newmdict, 'scriptlist': ['/sitemedia/js/fidositecore.js']})
            return render_to_response('membermanage/memberemailaddressupdate.html', cntxdict)
        else :
            cntxdict  = csrf(req)
            newmdict  = {'id' : member_id, 'form' : form, 'wizard': reverse('fidoonline.membermanage.membercreate.addaddress', args=[member_id])}
            newmdict['canurl'] = reverse('fidoonline.membermanage.memberviews.detailmemberframeset', args=[member_id])  
            cntxdict.update({'member' : newmdict, 'scriptlist': ['/sitemedia/js/fidositecore.js']})
            return render_to_response('membermanage/memberaddressupdate.html', cntxdict)

    elif req.POST.has_key('AddAddressButton') :
        cntxdict  = csrf(req)
        newmdict  = {'id' : member_id, 'form' : form, 'wizard': reverse('fidoonline.membermanage.membercreate.addaddress', args=[member_id])}
        newmdict['canurl'] = reverse('fidoonline.membermanage.memberviews.detailmemberframeset', args=[member_id])  
        cntxdict.update({'member' : newmdict, 'scriptlist': ['/sitemedia/js/fidositecore.js']})
        return render_to_response('membermanage/memberaddressupdate.html', cntxdict)
    elif req.POST.has_key('CancelAddressButton') :
        return HttpResponseRedirect(reverse('fidoonline.membermanage.memberviews.detailmemberframeset', args=[member_id]))
    else :    
        form = MailAddressForm()
        form.fields['street'].initial    = ''
        form.fields['city'].initial      = ''
        form.fields['state'].initial     = ''
        form.fields['zipcode'].initial   = ''
        form.fields['zipext'].initial    = ''
        cntxdict  = csrf(req)
        newmdict  = {'id' : member_id, 'form' : form, 'wizard': reverse('fidoonline.membermanage.membercreate.addaddress', args=[member_id])}
        newmdict['canurl'] = reverse('fidoonline.membermanage.memberviews.detailmemberframeset', args=[member_id])  
        cntxdict.update({'member' : newmdict, 'scriptlist': ['/sitemedia/js/fidositecore.js']})
        return render_to_response('membermanage/memberaddressupdate.html', cntxdict)
  
# -------------------------------------------------------------------------------------
@login_required
def addemail(req, member_id) :
    """
    detail/new/email/(?P<member_id>\d+)
    """
    form  = EMailAddressForm(req.POST)
    form.empty_permitted = True
    if req.POST.has_key('AddEMailAddressButton') and form.is_valid() :
        if not member_id :
            raise OperationalError("Asking for an email address change on an unknown member - Member should already exist")
        try :
            member =  Member.objects.get(pk=member_id)
        except Member.DoesNotExist :
            return HttpResponseNotFound(content="There is no record for Member ID %s" % (member_id))
        if hasattr(form, 'cleaned_data') :
            emailadr        = EMailAddress()
            emailadr.name   = form.cleaned_data.get('em_name')
            emailadr.domain = form.cleaned_data.get('em_domain')
            othermembersqset = Member.objects.filter(emailadr__name__exact=emailadr.name).filter(emailadr__domain__exact=emailadr.domain)
            if othermembersqset.count() == 0 :
                emailadr.save()
            else :
                emailadr =  othermembersqset[0].emailadr
            member.emailadr = emailadr
            member.save()
            form  =  TelNumberForm()
            form.fields['tf_area'].initial   = ''
            form.fields['tf_exch'].initial   = ''
            form.fields['tf_line'].initial   = ''
            form.fields['tf_ext'].initial    = ''
            cntxdict  = csrf(req)
            newmdict  = {'id' : member_id, 'form' : form, 'wizard': reverse('fidoonline.membermanage.membercreate.addphone', args=[member_id])}
            newmdict['canurl'] = reverse('fidoonline.membermanage.memberviews.detailmemberframeset', args=[member_id])  
            cntxdict.update({'member' : newmdict, 'scriptlist': ['/sitemedia/js/fidositecore.js']})
            return render_to_response('membermanage/membertelephoneupdate.html', cntxdict)
        else :
            cntxdict  = csrf(req)
            newmdict  = {'id' : member_id, 'form' : form, 'wizard': reverse('fidoonline.membermanage.membercreate.addemail', args=[member_id])}
            newmdict['canurl'] = reverse('fidoonline.membermanage.memberviews.detailmemberframeset', args=[member_id])  
            cntxdict.update({'member' : newmdict, 'scriptlist': ['/sitemedia/js/fidositecore.js']})
            return render_to_response('membermanage/memberemailaddressupdate.html', cntxdict)
            
    elif req.POST.has_key('AddEMailAddressButton') :    
        cntxdict  = csrf(req)
        newmdict  = {'id' : member_id, 'form' : form, 'wizard': reverse('fidoonline.membermanage.membercreate.addemail', args=[member_id])}
        newmdict['canurl'] = reverse('fidoonline.membermanage.memberviews.detailmemberframeset', args=[member_id])  
        cntxdict.update({'member' : newmdict, 'scriptlist': ['/sitemedia/js/fidositecore.js']})
        return render_to_response('membermanage/memberemailaddressupdate.html', cntxdict)
    elif  req.POST.has_key('CancelEMailAddressButton') :
        return HttpResponseRedirect(reverse('fidoonline.membermanage.memberviews.detailmemberframeset', args=[member_id]))
    else :
        form  =  EMailAddressForm()
        form.fields['em_name'].initial    = ''
        form.fields['em_domain'].initial  = ''
        cntxdict  = csrf(req)
        newmdict  = {'id' : member_id, 'form' : form, 'wizard': reverse('fidoonline.membermanage.membercreate.addemail', args=[member_id])}
        newmdict['canurl'] = reverse('fidoonline.membermanage.memberviews.detailmemberframeset', args=[member_id])  
        cntxdict.update({'member' : newmdict, 'scriptlist': ['/sitemedia/js/fidositecore.js']})
        return render_to_response('membermanage/memberemailaddressupdate.html', cntxdict)

# -------------------------------------------------------------------------------------
@login_required
def addphone(req, member_id) :
    """
    detail/new/phone/(?P<member_id>\d+)
    """
    ptype = lambda member : {'ina': 'Reinstate', 'exp': 'Renew', 'exn': 'Renew', 'act': 'Renew', 'inf': 'New', 'inc': 'New'}[getstatusstyle(member)]
    form  = TelNumberForm(req.POST)
    if req.POST.has_key('AddTelephoneButton') and form.is_valid() :
        if not member_id :
            raise OperationalError("Asking for a telephone number on an unknown member - Member should already exist")
        try :
            member =  Member.objects.get(pk=member_id)
        except Member.DoesNotExist :
            return HttpResponseNotFound(content="There is no record for Member ID %s" % (member_id))
        if hasattr(form, 'cleaned_data') :
            telnumber        = TelNumber()
            telnumber.area   = form.cleaned_data.get('tf_area')
            telnumber.exch   = form.cleaned_data.get('tf_exch')
            telnumber.number = form.cleaned_data.get('tf_line')
            telnumber.ext    = form.cleaned_data.get('tf_ext')
            othermembersqset = Member.objects.filter(telnumber__area__exact=telnumber.area).filter(telnumber__exch__exact=telnumber.exch).filter(telnumber__number__exact=telnumber.number).filter(telnumber__ext__exact=telnumber.ext)
            if othermembersqset.count() == 0 :
                telnumber.save()
            else :
                telnumber    = othermembersqset[0].telnumber
            member.telnumber = telnumber
            member.save()
            jform  = JournalForm()
            dform  = DuesForm()
            jform.fields['jf_subject'].initial = 'Payment'
            jform.fields['jf_comment'].initial = ''
            dform.fields['df_paytype'].initial = ptype(member)
            dform.fields['df_amount'].initial  = 0
            cntxdict  = csrf(req)
            newmdict  = {'id' : member_id, 'dform' : dform,  'jform' : jform, 'wizard': reverse('fidoonline.membermanage.membercreate.addduespayment', args=[member_id])}
            newmdict['canurl'] = reverse('fidoonline.membermanage.memberviews.detailmemberframeset', args=[member_id])  
            cntxdict.update({'member' : newmdict, 'scriptlist': ['/sitemedia/js/fidositecore.js']})
            return render_to_response('membermanage/memberduesadd.html', cntxdict)
        else :
            cntxdict  = csrf(req)
            newmdict  = {'id' : member_id, 'form' : form, 'wizard': reverse('fidoonline.membermanage.membercreate.addphone', args=[member_id])}
            newmdict['canurl'] = reverse('fidoonline.membermanage.memberviews.detailmemberframeset', args=[member_id])  
            cntxdict.update({'member' : newmdict, 'scriptlist': ['/sitemedia/js/fidositecore.js']})
            return render_to_response('membermanage/membertelephoneupdate.html', cntxdict)
    elif req.POST.has_key('AddTelephoneButton') :
        cntxdict = csrf(req)
        newmdict  = {'id' : member_id, 'form' : form, 'wizard': reverse('fidoonline.membermanage.membercreate.addphone', args=[member_id])}
        newmdict['canurl'] = reverse('fidoonline.membermanage.memberviews.detailmemberframeset', args=[member_id])  
        cntxdict.update({'member' : newmdict, 'scriptlist': ['/sitemedia/js/fidositecore.js']})
        return render_to_response('membermanage/membertelephoneupdate.html', cntxdict)
    elif  req.POST.has_key('CancelEMailAddressButton') :
        return HttpResponseRedirect(reverse('fidoonline.membermanage.memberviews.detailmemberframeset', args=[member_id]))
    else :
        form  =  TelNumberForm()
        form.fields['tf_area'].initial   = ''
        form.fields['tf_exch'].initial   = ''
        form.fields['tf_line'].initial   = ''
        form.fields['tf_ext'].initial    = ''
        cntxdict = csrf(req)
        newmdict  = {'id' : member_id, 'form' : form, 'wizard': reverse('fidoonline.membermanage.membercreate.addphone', args=[member_id])}
        newmdict['canurl'] = reverse('fidoonline.membermanage.memberviews.detailmemberframeset', args=[member_id])  
        cntxdict.update({'member' : newmdict, 'scriptlist': ['/sitemedia/js/fidositecore.js']})
        return render_to_response('membermanage/membertelephoneupdate.html', cntxdict)

# -------------------------------------------------------------------------------------
@login_required
def addduespayment(req, member_id) :
    """
    detail/new/payment/(?P<member_id>\d+)
    """
    ptype = lambda member : {'ina': 'Reinstate', 'exp': 'Renew', 'exn': 'Renew', 'act': 'Renew', 'inf': 'New', 'inc': 'New'}[getstatusstyle(member)]
    dform  = DuesForm(req.POST)
    jform  = JournalForm(req.POST)
    if req.POST.has_key('AddDuesButton') and dform.is_valid() and jform.is_valid() :
        if not member_id :
            raise OperationalError("Posting dues and related journal entry on an unknown member - Member should already exist.")
        try :
            member =  Member.objects.get(pk=member_id)
        except Member.DoesNotExist :
            return HttpResponseNotFound(content="There is no record for Member ID %s" % (member_id))
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
            pform = PetForm()
            tform = TagForm()
            cntxdict  = csrf(req)
            newmdict  = {'id' : member_id, 'pform' : pform, 'tform' : tform, 'wizard': reverse('fidoonline.membermanage.membercreate.addpet', args=[member_id])}
            newmdict['canurl'] = reverse('fidoonline.membermanage.memberviews.detailmemberframeset', args=[member_id])  
            cntxdict.update({'member' : newmdict, 'scriptlist': ['/sitemedia/js/fidositecore.js']})
            return render_to_response('membermanage/memberpetadd.html', cntxdict)
        else :
            cntxdict  = csrf(req)
            newmdict  = {'id' : member_id, 'dform' : dform,  'jform' : jform, 'wizard': reverse('fidoonline.membermanage.membercreate.addduespayment', args=[member_id])}
            newmdict['canurl'] = reverse('fidoonline.membermanage.memberviews.detailmemberframeset', args=[member_id])  
            cntxdict.update({'member' : newmdict, 'scriptlist': ['/sitemedia/js/fidositecore.js']})
            return render_to_response('membermanage/memberduesadd.html', cntxdict)
    elif req.POST.has_key('AddDuesButton') :
        cntxdict  = csrf(req)
        newmdict  = {'id' : member_id, 'dform' : dform,  'jform' : jform, 'wizard': reverse('fidoonline.membermanage.membercreate.addduespayment', args=[member_id])}
        newmdict['canurl'] = reverse('fidoonline.membermanage.memberviews.detailmemberframeset', args=[member_id])  
        cntxdict.update({'member' : newmdict, 'scriptlist': ['/sitemedia/js/fidositecore.js']})
        return render_to_response('membermanage/memberduesadd.html', cntxdict)
    else :
        jform  = JournalForm()
        dform  = DuesForm()
        try :
            member =  Member.objects.get(pk=member_id)
        except Member.DoesNotExist :
            return HttpResponseNotFound(content="There is no record for Member ID %s" % (member_id))
        jform.fields['jf_subject'].initial = 'Payment'
        jform.fields['jf_comment'].initial = ''
        dform.fields['df_paytype'].initial = ptype(member)
        dform.fields['df_amount'].initial  = 0
        cntxdict  = csrf(req)
        newmdict  = {'id' : member_id, 'dform' : dform,  'jform' : jform, 'wizard': reverse('fidoonline.membermanage.membercreate.addduespayment', args=[member_id])}
        newmdict['canurl'] = reverse('fidoonline.membermanage.memberviews.detailmemberframeset', args=[member_id])  
        cntxdict.update({'member' : newmdict, 'scriptlist': ['/sitemedia/js/fidositecore.js']})
        return render_to_response('membermanage/memberduesadd.html', cntxdict)

# -------------------------------------------------------------------------------------
@login_required
def addpet(req, member_id) :
    """
    detail/new/addpet/(?P<member_id>\d+)
    """
    ptype = lambda member : {'ina': 'Reinstate', 'exp': 'Renew', 'exn': 'Renew', 'act': 'Renew', 'inf': 'New', 'inc': 'New'}[getstatusstyle(member)]
    pform = PetForm(req.POST)
    tform = TagForm(req.POST)
    if req.POST.has_key('AddPetButton') and  pform.is_valid() and tform.is_valid() :
        member, newpet, newtag, newlink = util_registerpet(req, member_id, pform, tform)
        pform = PetForm()
        tform = TagForm()
        cntxdict  = csrf(req)
        newmdict  = {'id' : member_id, 'pform' : pform, 'tform' : tform, 'wizard': reverse('fidoonline.membermanage.membercreate.addpet', args=[member_id])}
        newmdict['canurl'] = reverse('fidoonline.membermanage.memberviews.detailmemberframeset', args=[member_id])  
        cntxdict.update({'member' : newmdict, 'scriptlist': ['/sitemedia/js/fidositecore.js']})
        return render_to_response('membermanage/memberpetadd.html', cntxdict)

    elif req.POST.has_key('AddPetButton') and pform.is_valid() :
        member, newpet, newtag, newlink = util_badtagonly(req, member_id, pform, tform)
        pform = PetForm()
        tform = TagForm()
        cntxdict  = csrf(req)
        newmdict  = {'id' : member_id, 'pform' : pform, 'tform' : tform, 'wizard': reverse('fidoonline.membermanage.membercreate.addpet', args=[member_id])}
        newmdict['canurl'] = reverse('fidoonline.membermanage.memberviews.detailmemberframeset', args=[member_id])  
        cntxdict.update({'member' : newmdict, 'scriptlist': ['/sitemedia/js/fidositecore.js']})
        return render_to_response('membermanage/memberpetadd.html', cntxdict)

    elif req.POST.has_key('DonePetButton') :
        if pform.is_valid() and tform.is_valid() :
            member, newpet, newtag, newlink = util_registerpet(req, member_id, pform, tform)
        elif  pform.is_valid() :
            member, newpet, newtag, newlink = util_badtagonly(req, member_id, pform, tform)
        else :
            member       = get_object_or_404(Member, pk=member_id)
            try:
                memberpref = MemberPreference.objects.get(pk=member.memberid)
            except MemberPreference.DoesNotExist :
                # If preferences are missing, the member is presumed to be in
                # a just-created state, for there (should be) a 1:1 correspondence
                # between members and their preferences.
                memberpref           = MemberPreference()
                memberpref.memberid  = member
                memberpref.prefs     = 'BroadcastEmail'
                memberpref.save()
        cntxdict = csrf(req)
        prefdict = mkmemberpreferences(member, reverse('fidoonline.membermanage.membercreate.addpreference', args=[member_id]))
        prefdict['wizard'] = reverse('fidoonline.membermanage.membercreate.addpreference', args=[member_id])
        prefdict['canurl'] = reverse('fidoonline.membermanage.memberviews.detailmemberframeset', args=[member_id])  
        cntxdict.update({'member' : prefdict, 'scriptlist': ['/sitemedia/js/fidositecore.js']})
        return render_to_response('membermanage/memberpreference.html', cntxdict)

    elif req.POST.has_key('CancelPetButton') :
       return HttpResponseRedirect(reverse('fidoonline.membermanage.memberviews.detailmemberframeset', args=[member_id]))
    else :
        pform = PetForm()
        tform = TagForm()
        cntxdict = csrf(req)
        newmdict  = {'id' : member_id, 'pform' : pform, 'tform' : tform, 'wizard': reverse('fidoonline.membermanage.membercreate.addpet', args=[member_id])}
        newmdict['canurl'] = reverse('fidoonline.membermanage.memberviews.detailmemberframeset', args=[member_id])  
        cntxdict.update({'member' : newmdict, 'scriptlist': ['/sitemedia/js/fidositecore.js']})
        return render_to_response('membermanage/memberpetadd.html', cntxdict)

# -------------------------------------------------------------------------------------
@login_required
def addpreference(req, member_id) :
    """
    detail/new/setmemberpreference/(?P<member_id>\d+)
    """
    if req.POST.has_key('CopyPrefsButton') :
#       flag = pydb.debugger()
        cntxdict = csrf(req)
        newmdict  = {'id' : member_id, 'wizard': reverse('fidoonline.membermanage.membercreate.copymodifymember', args=[member_id])}
        newmdict['canurl'] = reverse('fidoonline.membermanage.memberviews.detailmemberframeset', args=[member_id])  
        cntxdict.update({'member' : newmdict, 'scriptlist': ['/sitemedia/js/fidositecore.js']})
        return render_to_response('membermanage/membernameupdate.html', cntxdict)
        
    elif req.POST.has_key('ReviewPrefsButton') :    
        return HttpResponseRedirect(reverse('fidoonline.membermanage.memberviews.detailmemberframeset', args=[member_id]))
    else :
        member, memberpref = util_setmemberpreferences(req, member_id);
        cntxdict = csrf(req)
        prefdict = mkmemberpreferences(member, reverse('fidoonline.membermanage.membercreate.addpreference', args=[member_id]))
        prefdict['wizard'] = reverse('fidoonline.membermanage.membercreate.addpreference', args=[member_id])
        prefdict['canurl'] = reverse('fidoonline.membermanage.memberviews.detailmemberframeset', args=[member_id])  
        cntxdict.update({'member' : prefdict, 'scriptlist': ['/sitemedia/js/fidositecore.js']})
        return render_to_response('membermanage/memberpreference.html', cntxdict)
 
# -------------------------------------------------------------------------------------
@login_required
def copymodifymember (req, member_id) :
    """
    detail/new/copymodifymember/(?P<member_id>\d+)
    """
    if not member_id :
        raise OperationalError("Posting dues and related journal entry on an unknown member - Member should already exist.")
    try :
        basemember =  Member.objects.get(pk=member_id)
    except Member.DoesNotExist :
        return HttpResponseNotFound(content="There is no record for Member ID %s" % (member_id))
    newmember = Member()
    newmember.mailadr   = basemember.mailadr
    newmember.telnumber = basemember.telnumber
    newmember.emailadr  = basemember.emailadr
    newmember.save()
    newmember_id = str(newmember.memberid)
    return HttpResponseRedirect(reverse('fidoonline.membermanage.memberviews.detailmemberframeset', args=[newmember_id]))

    
