"""
petviews.py
HTTP request object processors for the membermanage 
  application.
"""

from django                             import forms
from django.contrib.auth.decorators     import login_required
from django.core.context_processors     import csrf
from django.core.urlresolvers           import reverse
from django.db                          import transaction
from django.forms.util                  import ErrorList
from django.http                        import HttpResponseRedirect, HttpResponse
from django.shortcuts                   import render_to_response, get_object_or_404
from django.template                    import Context, loader
from fidoonline.membermanage.forms      import Lookup
from fidoonline.membermanage.memberutil import mkmembercontactdictionary, mkmemberpetlist, mkmemberpicker, mknonmemberpetlist
from fidoonline.membermanage.models     import Member, MemberPet, Pet, DogTag, EMailAddress, TelNumber
# import pydb
# -------------------------------------------------------------------------------------
@login_required
def listpets(req) :
    """
    Build an overview list of pets to be rendered through the plist.html template
    """

    from django.db.models import Q

    headers = (
               {'name': 'Record Number', 'width': 200},
               {'name': 'Name',          'width': 200},
               {'name': 'Description',   'width': 450},
               {'name': 'Dog Tag',       'width': 200}
              )
    displayitems = []
    owners       = []
    if (req.method == 'POST') :
        lookup = Lookup(req.POST)
        lookup.searchagent = reverse('fidoonline.membermanage.petviews.listpets')
        if lookup.is_valid() :
            fstring = lookup.cleaned_data['lu_search']
            if hasattr(fstring, 'isdigit') and fstring.isdigit() :
                pets    = Pet.objects.filter(dogtag__tagnumber__exact=int(fstring))
            elif hasattr(fstring, 'isalpha') and fstring.isalpha() :  
  
                pets    = Pet.objects.filter(name__icontains=fstring)
            else :
                pets    = Pet.objects.all()
        else :
            pets    = Pet.objects.all()
    else :
        pets  = Pet.objects.all()
        lookup = Lookup()
        lookup.searchagent = reverse('fidoonline.membermanage.petviews.listpets')
    for pet in pets :
        owners   = []
        pet.stat = 0
        if not (hasattr(pet, 'description')) or pet.description == None :
            pet.stat += 1
            pet.description = ''
        pet.stat *= 2    
        dtqueryset  = DogTag.objects.filter(petid__exact=pet.petid)
        if dtqueryset.count() == 0 :
            pet.stat += 1
            dogtag = DogTag()
        else :
            dogtag = dtqueryset[0]
        pet.stat *= 2    
        mqueryset = Member.objects.filter(pet__petid__exact=pet.petid)
        if mqueryset.count() == 0 :
            pet.stat += 1
        else :
            for m in mqueryset :
                m.stat = 0
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

                owners.append(
                                {
                                   'name'       : ' '.join(strng),
                                   'identifier' : m.memberid,
                                   'email'      : {'err' : False, 'address' : '%s@%s' % (m.emailadr.name, m.emailadr.domain)},
                                   'telephone'  : {'err' : False, 'number'  : '%s-%s-%s' % (m.telnumber.area, m.telnumber.exch, m.telnumber.number)}
                                }
                             )
                if m.stat & 1 :
                    owners[-1]['telephone']['err'] = True
                if m.stat & 2 :
                    owners[-1]['email']['err']     = True

        displayitems.append(
                              {
                                 'identifier'    : pet.petid,
                                 'name'          : pet.name,
                                 'description'   : {'err' : False, 'text'   : pet.description},
                                 'dogtag'        : {'err' : False, 'number' : dogtag.tagnumber},
                                 'member'        : {
                                                     'err' : False,
                                                     'owners'  : owners
                                                   }
                              }
                           )
        if pet.stat & 1 :
            displayitems[-1]['member']['err'] = True
        if pet.stat & 2 :
            displayitems[-1]['dogtag']['err'] = True
        if pet.stat & 4 :
            displayitems[-1]['description']['err'] = True
    return render_to_response('membermanage/plist.html', {'lookup': lookup, 'pet_names': displayitems, 'table_headers': headers, 'window_title': "Pet Directory", 'page_title': 'Member Pet Directory'})
# -------------------------------------------------------------------------------------
@login_required
def listtags (req) :
    """
    Overview list of FIDO tagged dogs to be rendered through the taglist.html template. 
    """

    headers = (
                {'name' : "Dog Tag(s) & Status",   'width' : 200},
                {'name' : "Pet's Name",            'width' : 100},
                {'name' : "Member Identifiers",    'width' : 100},
                {'name' : "Associated Members",    'width' : 200},
                {'name' : "EMail",                 'width' : 200},
                {'name' : "Telephone(s)",          'width' : 200}
              )
    crumbs  = ({'label': 'Start Here', 'link': reverse('fidoonline.membermanage.starthereview.start')}, {'label': 'Tag Directory', 'link': None})    

    # Tagged pets in pset, a Query set; rows a display row container of dictionaries.
    rows    = list()
    extra   = list()
    pset    = Pet.objects.filter(dogtag__tagstatus__in=['Assigned', 'Lost'])
    for pet in pset:
        if len(rows) and pet.petid == rows[-1]['ident'] :
            continue
        else :
            # Detail link - using (arbitrarily) first of what could be a number of names
            first_member = pet.memberrel.iterator().next()
            if first_member.emailadr != None :
                emlink = "mailto:%s@%s" % (first_member.emailadr.name, first_member.emailadr.domain)
            else :
                emlink = None
            eml  = list()
            tell = list()
            for m in pet.memberrel.iterator() :
                # EMails
                if m.emailadr != None:
                    eml.append("%s@%s" % (m.emailadr.name, m.emailadr.domain))
                else :
                    eml.append("<No email>")
                # Telephones
                if m.telnumber != None:
                    tell.append("%03d-%03d-%04d" % (m.telnumber.area, m.telnumber.exch, m.telnumber.number))
                else :
                    tell.append("<No telephone>")
            tell = list(set(tell))
            eml  = list(set(eml))
            rows.append(
                         {
                            'tags'       : ", ".join(map(lambda t: "%04d (%s)" % (t.tagnumber, t.tagstatus), pet.dogtag_set.iterator())),
                            'name'       : pet.name,
                            'ident'      : pet.petid,
                            'members'    : ", ".join(map(lambda m: "%05d" % (m.memberid), pet.memberrel.iterator())),
                            'assocs'     : ", ".join(map(lambda m: "%s %s" % (m.first, m.last), pet.memberrel.iterator())),
                            'emails'     : ", ".join(eml),
                            'telephones' : ", ".join(tell),
                            'link'       : reverse('fidoonline.membermanage.memberviews.detailmemberframeset', args=[first_member.memberid]),
                            'emlink'     : emlink
                         }
                       )

            tnlst = [t.tagnumber for t in pet.dogtag_set.iterator()]
            for chkd, tn in enumerate(tnlst) :
                if chkd :
                    extra.append(rows[-1].copy())
                    extra[-1]['indx'] = tn
                else :    
                    rows[-1]['indx'] = tn
    rows = rows + extra            
    rows.sort(key=lambda ritm: ritm['indx']) 
    return render_to_response('membermanage/taglist.html', { 'crumbline' : crumbs, 'pets': rows, 'table_headers': headers, 'window_title': "Dog Tag List", 'page_title': 'List of Distributed FIDO Tags'})
# -------------------------------------------------------------------------------------
@login_required
def detailonepet (req, pet_id) :
    """
    """
    def mktagset(in_pet) :
        return map(lambda t: {'number': t.tagnumber, 'status': t.tagstatus}, in_pet.dogtag_set.all())
    
    # --- Get various factoids --- 
    msgset   = []
    #Pet
    pet      = get_object_or_404(Pet, pk=pet_id)
    #Owner(s)
    if pet.memberrel.count() == 0 :
        msgset.append("WARNING! %s does not seem to be associated with any member of FIDO. There is a stray dog in the database! Contact the membership chair; send that worthy the URL to this page. Thank you!" % (str(pet)))
        ownrdicts = copets = dogtags = None
    else :

        ownrdicts = map(lambda member: mkmembercontactdictionary(member), pet.memberrel.all())
        for ownr in ownrdicts :
            ownr.update({'link': reverse('fidoonline.membermanage.memberviews.detailmemberframeset', args=[ownr['id']])})
        # Co_pets (assuming first owner has the same Member<->Pet
        # relationships of all the other owners. Weed out selected pet
        # because this view is mostly about that critter; no need for it
        # to be in the co-pet listings.
        mcnt    = pet.memberrel.count()
        ps      = ["", "s"][int(mcnt != 1)]
        msgset.append("%s owns %d FIDO member%s." % (pet.name, mcnt, ps))
        co_pets = filter(lambda p: p != pet, pet.memberrel.all()[0].pet_set.all())
        copets  = map(lambda p : {'name': p.name, 'link' : reverse('fidoonline.membermanage.petviews.detailonepet', args=[p.petid]), 'dogtags': mktagset(p)}, co_pets) 

    # --- Populate context ---
    context = {
                'messages'      : msgset,
                'identifier'    : pet.petid,
                'name'          : pet.name,
                'description'   : pet.description,
                'dogtags'       : mktagset(pet),
                'member'        : ownrdicts,
                'copets'        : copets
              }
    context.update(csrf(req))
        
    # Render context through the pet detail view page
    return render_to_response('membermanage/petdetail.html', context)
# -------------------------------------------------------------------------------------
def initializepetform(formdict) :
    """
    Adding new pet. Initialize form. 
    """
# -------------------------------------------------------------------------------------
@transaction.commit_manually
def processpetpost (req, member_id, formdict) :
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

    pass
