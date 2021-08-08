"""memberutil:

Functions in this module build dictionaries suitable for use as
mappings between variables used in various member view request-reply
hander routines and variables in templates i.e., these utility
functions build context dictionaries. Nearly all of these utility
functions generate context dictionaries for the membertable.html
template, the standard table used in the small quadrants that comprise
the detail ('release two') display."""

from django                         import forms
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers       import reverse
from django.db.models               import Q
from django.forms.util              import ErrorList
from django.http                    import HttpResponseRedirect, HttpResponse
from django.shortcuts               import render_to_response, get_object_or_404
from fidoonline.membermanage.forms  import DuesForm, EMailAddressForm, EmptyForm, JournalForm, Lookup, MailAddressForm, MemberForm, PetForm, TelNumberForm
from fidoonline.membermanage.models import MailAddress, TelNumber, EMailAddress, Member, MemberPet, Pet, DogTag, MemberPreference, Journal, Dues

# import pydb
# -------------------------------------------------------------------------------------
def getstatusstyle(member) :
    """
    Map days to (or after) expiry to CSS stylesheet color codes.
    See membermanage.css 
    """
    try :
        expiry = member.term['expiry']
        if expiry :
            return ['ina', 'exp', 'exn', 'act'][(int(expiry > 90)*4 + int(expiry <= 90 and expiry >   0) * 3 + int(expiry <=  0 and expiry > -90)*2 + int(expiry <= -90)) - 1]
        else :
            return 'inc'
    except RuntimeError, m :
        # Very new members will not have a defined expiry date. Return 'inc' (incomplete) style
        lmsg  = str(m)
        if lmsg.find('no payment records') >= 0 : #FIXME: Define a particular 'no records' exception
            return 'inc'
        else :
            raise RuntimeError("{0} has no defined expiry.".format(repr(member)))
        
# ---------------------------------------------------------------------------
def updateformsec(map, dat_dict, form_dict) :
    """
    """
    for df, ff in map.iteritems() :
        dat_dict.__dict__[df] = form_dict.cleaned_data[ff]
# ---------------------------------------------------------------------------
def mkmembercontactdictionary(member) :
    """
    member: a Member db object
    """
    strng = []
    for i in (member.salute, member.first, member.middle, member.last, member.suffix) :
        if len(i) : strng.append(i)
    if member.mailadr != None :
        loc = []
        for i in (member.mailadr.street, member.mailadr.aptnum) :
            if len(i) : loc.append(i)
        maildict = {
                      'business'     : member.mailadr.company,
                      'location'     : ' '.join(loc),
                      'citystatezip' :  "%s, %s %s-%s" % (member.mailadr.city, member.mailadr.state, member.mailadr.zipcode, member.mailadr.zipext)   
                   }
    else :
        maildict = None
    if member.telnumber != None :
        tel = "%s" % (str(member.telnumber))
    else :
        tel = None
    if member.emailadr != None :
        eml = "%s@%s" % (member.emailadr.name, member.emailadr.domain)
    else : eml = None
    stat = getstatusstyle(member)
    returndict =  {
                   'email'       : unicode(eml), 
                   'fullname'    : ' '.join(strng),
                   'id'          : unicode(member.memberid),
                   'statusstyle' : stat,
                   'street'      : maildict,
                   'telephone'   : unicode(tel), 
                  }
    return returndict
# ---------------------------------------------------------------------------
def mknonmemberdictionary(member_id) :
    """
    """
    returndict =  {
                   'email'       : " ", 
                   'fullname'    : 'Unassigned',
                   'id'          : unicode(member_id),
                   'statusstyle' : 'inf',
                   'street'      : {'business' : " ", 'location' : " ", 'citystatezip' : " "},
                   'telephone'   : " ", 
                  }
    return returndict
# -------------------------------------------------------------------------------------
def mknonmemberdueslist (member_id) :
    """
    Populate a dictionary that will generate an unpopulated dues display for a non-member
    """
    member                 = dict()
    member['action']       = ""
    member['coltitles']    = ""
    member['detail']       = []
    member['doc']          = 'Dues summary table has no entries; the member id %s has not been assigned.' % (member_id)
    member['innerwidths']  = [110, 130, 120, 120]
    member['msg']          = "No dues records are available: %s is not assigned." % (member_id)
    member['msgspan']      = 0
    member['outerwidths']  = [110, 122, 114, 134]
    member['size']         = len(member['outerwidths'])
    member['statusstyle']  = 'inf'
    member['title']        = "Dues Review"
    return member
# -------------------------------------------------------------------------------------
def mkmemberdueslist (member, actionurl) :
    """
    Populate a dictionary that will furnish a membertable small display with a member's
    dues payment history.
    """
    import datetime as dt
    try:
        expiry               = member.term['expiry']
    except RuntimeError, m:
        # Partial wizard record: dues data have not been gathered yet.
        expiry = 0
    ess                  = "s"
    if abs(expiry) == 1 :
        ess              = ""
    rset                 = dict()
    rset['action']       = actionurl
    rset['coltitles']    = ["Entry Number", "Date", "Amount", "Type"]
    rset['detail']       = dset = list()
    duesquerysset        = Dues.objects.filter(memberid__exact=member.memberid)
    for de in duesquerysset :
        dset.append((
                      {'align': 'left',  'data': "%d" % (de.duesid)},
                      {'align': 'left',  'data': "%s" % (de.paydate.strftime('%b %d %Y'))},
                      {'align': 'right', 'data': "%s" % (de.payamount)},
                      {'align': 'left',  'data': "%s" % (de.paytype)},
                   ))
    rset['doc']          = 'Dues summary table for %s.' % unicode(member.memberid)
    rset['innerwidths']  = [108, 117, 122, 152]
    now    = dt.datetime.now()
    if expiry > 0 :
        rset['msg']      = "%d day%s until expiry, as of %s. Term ends %s." % (expiry, ess, now.strftime('%b %d %Y'), member.term['end'].strftime('%b %d %Y'))
    elif expiry == 0 :
        try :
            if hasattr(member.term['end'], 'strftime') :
                rset['msg']  = "Member's term expires today, %s." % (member.term['end'].strftime('%b %d %Y'))
        except RuntimeError, m :
            rset['msg']  = "Member has not paid any dues; no term has been established."
    else :
        rset['msg']      = "%d day%s since expiry, as of %s. Term ends %s." % (abs(expiry), ess, now.strftime('%b %d %Y'), member.term['end'].strftime('%b %d %Y'))
    rset['msgspan']      = len(rset['innerwidths']) - 1
    rset['outerwidths']  = [110, 115, 120, 154]
    rset['size']         = len(rset['outerwidths'])
    rset['statusstyle']  = getstatusstyle(member)
    rset['title']        = "Dues Review"
    rset['widgetset' ]   = [{'name': 'PaymentButton', 'value': 'Add Payment'}]
    return rset
# -------------------------------------------------------------------------------------
def mknonmemberpetlist(member_id) :
    """
    Populate a dictionary that will generate an unpopulated pet display for a non-member
    """
    petlist                 = dict()
    petlist['doc']          = "No pets are available: %s is not assigned." % (member_id)
    petlist['msg']          = "No pets are available: %s is not assigned." % (member_id)
    petlist['msgspan']      = 0
    petlist['size']         = 1
    petlist['statusstyle']  = 'inf'
    return petlist
# -------------------------------------------------------------------------------------
def  mkmemberpetlist(member, actionurl) :
    """
    Make a listing of Pets associated with the member through the MemberPet mapping relation.
    Table rows each have a per-pet-row edit button to access pet name, description and associated Dog
    Tag, if any. table itself has a share button to associate pets on table with other Fido members
    """
    def mkbutton(member, pet) :
        """
        Make an HTML button to trigger the edit of a particular pet
        """
        buttondict = {'type': 'submit', 'name': 'ChangePetButton', 'value': 'Edit', 'agent': reverse('fidoonline.membermanage.memberactions.changepet', args=[member.memberid, pet.petid])}
        return buttondict
    # ---------------------------------------------------------------------------------    
    petlist = dict()
    petlist['action']       = actionurl
    petlist['coltitles']    = ["ID", "Name", "Description", "Tags", "Status", "Shared", "Change"]
    petlist['detail']       = detail = list()
    petqueryset = MemberPet.objects.filter(member__exact=member.memberid)
    if petqueryset.count() > 1 :
        ess  = "s"
        ess2 = ""
    else :
        ess  = ""
        ess2 = "s"
    for pid in petqueryset :
        cpet      = Pet.objects.get(pk=pid.pet.petid)
        tagqs     = DogTag.objects.filter(petid__exact=cpet.petid)
        coownqset = MemberPet.objects.filter(pet__exact=cpet.petid)
        if tagqs.count() > 0 :
            tagnm = ""
            tagst = ""
            for tag in tagqs :
                tagnm = "%s %d<br />" % (tagnm, tag.tagnumber)
                tagst = "%s %s<br />" % (tagst, tag.tagstatus)
        else :
            tagnm = "None"
            tagst = "None"
        if coownqset.count() > 0 :
            coown = list()
            for own in coownqset :
                if own.member.memberid != member.memberid : 
                    coown.append({'own': "%s %s" % (own.member.first, own.member.last), 'target': reverse('fidoonline.membermanage.memberviews.detailmemberframeset', args=[own.member.memberid])})
            if len(coown) == 0 :
                coown = None
            else :
                coown = {'coowners' : coown}
        else :
            coown = None
        detail.append((
                        {'align': 'left',   'data': "%d" % (cpet.petid)},
                        {'align': 'left',   'data': "%s" % (cpet.name)},
                        {'align': 'left',   'data': "%s" % (cpet.description)},
                        {'align': 'left',   'data': "%s" % (tagnm)},
                        {'align': 'left',   'data': "%s" % (tagst)},
                        {'align': 'left',   'data': coown},
                        {'align': 'left',   'data': mkbutton(member, cpet)}
                     ))
    petlist['doc']          = 'Pets who own %s' % (unicode(member))
    petlist['innerwidths']  = [37, 50, 180, 50, 50, 50, 23]
    if petqueryset.count() > 0 :
        petlist['msg']      = "%d pet%s own%s member %s" % (petqueryset.count(), ess, ess2, unicode(member))
    else :
        petlist['msg']      = "No pets own member %s" % (unicode(member)) 
    petlist['outerwidths']  = [40, 50, 180, 50, 50, 50, 20]
    petlist['size']         = len(petlist['outerwidths'])
    petlist['statusstyle']  = getstatusstyle(member)
    petlist['title']        = "Pet Listing"
    if petqueryset.count() > 0 :
        petlist['widgetset']    = [{'name': 'SharePetButton', 'value': 'Share Pet'}, {'name': 'AddPetButton', 'value': 'Add Pet'}]
    else :    
        petlist['widgetset']    = [{'name': 'AddPetButton', 'value': 'Add Pet'}]
    petlist['msgspan']      = petlist['size'] - len(petlist['widgetset'])
    return petlist
    
# ---------------------------------------------------------------------------
def find_member_submit(req) :
    """
    Construct a regular expression to find strings of the form 'MID-<ddddd>';
    angle brackets and characters within are meta-notation and indicate a five
    digit member identifier. Such among the keys of POST queries indicate the
    present of pressed 'member submit buttons' coming from browser FORMs that
    have been constructed, in part, by memberutil.mkmemberpicker. If one such
    string is found (and there can *only* be one because the user cannot press
    multiple submit buttons...), return the corresponding memberID, recovering
    it from the string, else return None, to indicate no such string (or implied
    button press) is within the POST mapping.  
    """
    import re
        
    tagre  = re.compile(r'^MID-(?P<id>\d+)')
    mfunc  = lambda k : tagre.match(k)
    pks    = filter(mfunc, req.POST.keys())
    if len(pks) > 0 :
        member_id = None
        mo        = tagre.match(pks.pop())
        return unicode(int(mo.groupdict()['id']))
# -------------------------------------------------------------------------------------
def mkmemberpicker (req, action, target, jsaction=None, banner=False) :
    """
    Generate a selection table - a context dictionary suitable for
    membertable.html and friends, populated with all member names
    (initially) but with a reduction search filter box (specifically,
    a Lookup form. Render the member names as Submit buttons and embed
    each in its own FORM; target the form as furnished by the caller.
    Request responders should process the results of such buttons with
    fidoonline.membermanage.memberutil.find_member_submit, immediately
    above. Optional jsaction, if present, will induce a second submit
    button to appear to the right of the search submit button. Populate
    with a 4-tuple: name, a string; value, a string (button label);
    javascript function name, string value that references a pre-loaded
    Javascript function, and the javascript function argument list, a
    string of comma-separated arguments. (To date, such functions are
    like startWizardWindow() in /sitemedia/js/fidositecore.js and
    start up a mini browser window to run a wizard sequence.)
    
    """
    searchdict = {}
    searchdict['lookup'] = lu = Lookup(req.POST) 
    if lu.is_valid() and 'lu_search' in req.POST :
        filterstring = lu.cleaned_data['lu_search']
        memberqset   = Member.objects.filter(Q(first__icontains=filterstring) | Q(last__icontains=filterstring) | Q(memberid__icontains=filterstring))
    else :
        memberqset   = None
    if memberqset and hasattr(memberqset, 'count') :
        if memberqset.count() > 0 :
            searchdict['title']    = 'Membership Search Results'
            searchdict['tabdat']   = tabdat = {}
            tabdat['rows'] = rows  = list()
            for mbr in memberqset :
                rows.append({'ID' : unicode(mbr.memberid), 'Member' : "%s %s" % (mbr.first, mbr.last), 'Pick' : "MID-%05d" % (mbr.memberid), 'target': target})
            tabdat['coltitle']     = 'Choose:'
            tabdat['widths']       = 500
            tabdat['title']        = "Member Search"
            tabdat['msg']          = "%d Members match '%s'" % (memberqset.count(), filterstring)
    else :
        searchdict['title']        = 'No Matches'
    searchdict['sfvalue']          = 'Find'
    searchdict['sfname']           = 'DoMemberSearch'
    searchdict['template']         = 'membermanage/memberpick.html'
    searchdict['action']           = action
    # Javascript wizard?
    if jsaction :
        searchdict['addjsaction'] = {'name': jsaction[0], 'value': jsaction[1], 'action': "%s('%s')" % (jsaction[2], jsaction[3])}
    if banner :
        searchdict['banner']      = True
    return searchdict        
# -------------------------------------------------------------------------------------
def  mkjournallist (member, actionurl) :
    """
    Generate a list of Journal entries that have been posted to the member's ID number
    """
    jrnlist                 = dict()
    jrnlist['action']       = actionurl
    jrnlist['coltitles']    = ["Entry #", "Date", "Subject", "Detail"]
    jrnlist['detail']       = dset = list()
    jrnlqueryset            = Journal.objects.filter(memberid__exact=member.memberid)
    for je in jrnlqueryset :
        dset.append((
                      {'align': 'left', 'data': "%d" % (je.journalid)},
                      {'align': 'left', 'data': "%s" % (je.entrydate.strftime('%b %d %Y'))},
                      {'align': 'left', 'data': "%s" % (je.entrytype)},
                      {'align': 'left', 'data': "%s" % (je.comment)},
                   ))
    jrnlist['doc']          = 'Journal entries for %s.' % (unicode(member.memberid))
    jrnlist['innerwidths']  = [80, 80, 80, 280]
    jrnlist['msg']          = '%d Journal entries for %s.' % (jrnlqueryset.count(), unicode(member.memberid))
    jrnlist['msgspan']      = len(jrnlist['innerwidths']) - 1
    jrnlist['outerwidths']  = [80, 80, 80, 280]
    jrnlist['size']         = len(jrnlist['innerwidths'])
    jrnlist['statusstyle']  = getstatusstyle(member)
    jrnlist['title']        = "Member Journal"
    jrnlist['widgetset' ]   = [{'name': 'JournalButton', 'value': 'Make Entry'}]
    return jrnlist
# -------------------------------------------------------------------------------------
def mknonmemberjournallist(member_id) :
    """
    """
    jrnlist                 = dict()
    jrnlist['doc']          = "No journal entries are available: %s is not assigned." % (member_id)
    jrnlist['msg']          = "No journal entries are available: %s is not assigned." % (member_id)
    jrnlist['msgspan']      = 0
    jrnlist['size']         = 1
    jrnlist['statusstyle']  = 'inf'
    return jrnlist
# -------------------------------------------------------------------------------------
def mknonmemberpreferences (member_id) :
    """
    Populate a dictionary that will generate an unpopulated preference display for a non-member
    """
    preflist                 = dict()
    preflist['doc']          = "No preferences are available: %s is not assigned." % (member_id)
    preflist['msg']          = "No preferences are available: %s is not assigned." % (member_id)
    preflist['msgspan']      = 0
    preflist['size']         = 1
    preflist['statusstyle']  = 'inf'
    return preflist
# -------------------------------------------------------------------------------------
def mkmemberpreferences (member, actionurl) :
    """
    Fabricates a context dictionary intended to be sent with the venerable membertable.html template;
    this a simple pairing of a preference statement and a checkbox indicating whether it is selected.
    The number of preferences is inherently open-ended, but has been two for a number of years now.
    This builds a one-row table, laying out preferences and their associated states horizontally -
    not a satisfactory case if the number of preferences grows beyond four or five. FIXME Preferences is
    slated for reorganizatin at the db level to be a simple key-value pair table, so that applications
    can decide what preferences they want without having the type and number of choices fixed, as
    it is now by the MemberPreference Preferences field, a predefined set of choices.
    """
    def mkbutton (bname, bvalue, actionurl) :
        """
        Make an dictionary to render (in the template) an
        HTML submit button with either 'Add' or 'Remove' to set/unset a preference 
        """
        return {'type': 'submit', 'name': bname, 'value': ['Add', 'Remove'][int(bvalue)], 'agent': actionurl}
        
        # -----------------------------------------------------------------------------

    msgtxt                   = "You may ADD the preference if the member does not yet have it; otherwise, you may REMOVE a preference the member currently has."
    preflist                 = dict()
    preflist['action']       = actionurl
    preflist['detail']       = dset = list()
    preflist['coltitles']    = ["With this preference:", "Do:"]
    preflist['innerwidths']  = preflist['outerwidths'] = [400, 100]
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
        
    preflst                  = memberpref.prefs.split(',')
    for tuplet in memberpref.prefclasses :
        dset      += [({'align': 'left', 'data': tuplet[1]}, {'align': 'left', 'data': mkbutton(tuplet[0], tuplet[0] in preflst, actionurl)})] 
    preflist['doc']          = msgtxt
    preflist['msg']          = msgtxt
    preflist['size']         = len(preflist['innerwidths'])
    preflist['msgspan']      = preflist['size']
    preflist['statusstyle']  = getstatusstyle(member)
    preflist['title']        = "Preferences for %s" % (unicode(member))         
    return preflist

# Lists of Journal entries
# -----------------------------------------------------------------------
def mkjournalentrylist(requestfilter) :
    """
    Generate a sequence of Journal entries, each satifying criteria in a  
    requestfilter dictionary:
    {
      'basedate': datetime -  journal entries made on or after 12:00 AM on this date.
                              if the key/value specification is omitted from the request
                              filter, and duration omitted as well, journal entries
                              will not be date-filtered.
      'duration': integer  -  days after basedate when the end date occurs; journal
                              entries on the end date up to 11:59.999... PM} will be
                              included in the set. If zero, or omitted, only
                              entries made on the base date would be included.
                              If both basedate and duration are omitted, journal
                              entries will not be filtered by date.
      'subjects': string set- Set of Journal.entryclasses (See class Journal
                              in model.py).These are the single word subjects
                              defined in the first of each (subject, description)
                              tuple that comprises Journal.entryclasses.
                              If the set is empty, nothing will be returned.
                              if the key/value is omitted, journal entries
                              will not be filtered by subject. Otherwise, a
                              union of all journal entries matching subjects
                              contained in the set will be included.
      'memberid': int set   - Filter for set of MemberID. If the set
                              is empty, nothing will be returned. If the key/value
                              is omitted, journal entries will not be filtered
                              by member identifiers.
      'comment' : string    - Filter comments for a matching pattern, a
                              substring. This is a simple pattern match; not
                              a regular expression.
    }                         
                             
    Returns a django.db.models.query.QuerySet which can be empty.
    """

    # -------------------------------------------------------------------
    def mk_period_filter(qs, rfdict):
        """
        Set duration, return modified query set qs. Duration is simply
        the day in rfdict['basedate'] when rfdict has no duration
        entry; it is basedate + duration inclusive otherwise.
        """
        import datetime as dt
        
        sd = rfdict['basedate']
        if rfdict.has_key('duration') :
            ed = sd + dt.timedelta(days=rfdict['duration'] + 1)
        else :
            ed = sd + dt.timedelta(days= 1) 
        return qs.filter(entrydate__gte=sd).filter(entrydate__lte=ed)
    # -------------------------------------------------------------------
    def mk_subject_filter(qs, rfdict):
        """
        Filter the given query set to include just those journal
        entries with the specified subjects. Return the filtered
        queryset
        """
        return qs.filter(entrytype__in=rfdict['subjects'])
    # -------------------------------------------------------------------
    def mk_memberid_filter(qs, rfdict):
        """
        Filter the given query set to include just those journal
        entries belonging to those members with the specified
        identifiers. Return the filtered queryset
        """
        return qs.filter(memberid__in=rfdict['memberid'])
    # -------------------------------------------------------------------
    def mk_comment_filter(qs, rfdict):
        """
        Filter the given query set to include just those journal
        entries with comments that contain the (simple) string
        pattern. This pattern is not a Regular Expression; it is
        a literal substring only.  
        """
        return qs.filter(comment__icontains=rfdict['comment'])

    ddict = {
                'basedate': mk_period_filter,
                'subjects': mk_subject_filter,
                'memberid': mk_memberid_filter,
                'comment' : mk_comment_filter
            }
    # -------------------------------------------------------------------
    def dispatch(qs, i, requestfilter) :
        try:
            return ddict[i](qs, requestfilter)
        except KeyError :
            return qs

    qset  = Journal.objects.all()
    for key in requestfilter.iterkeys() :
        qset  = dispatch(qset, key, requestfilter)
    return qset
    
# -----------------------------------------------------------------------
def mkjournalentrydisplaytable(requestfilter) :
    """
    Convenience function which can be put in the place of a dictionary
    parameter for a django.shortcuts.render_to_response utility. For the
    guts of generating the query, see mkjournalentrylist, above.
    requestfilter: dictionary - keys corresponds to Journal model fields
                                values correspond to where clause filters
    returns a context dictionary
    """
    import datetime as dt

    qset    =  mkjournalentrylist(requestfilter).order_by('-entrydate')
    cdict = {
              'journal_headers' : (
                                   {'name': 'Member ID',     'width':60},
                                   {'name': 'Member',        'width':120},
                                   {'name': 'Entry Date',    'width':170},
                                   {'name': 'Subject',       'width':110},
                                   {'name': 'Journal Entry', 'width':270} 
                                  )
            }
    elist = list()

    for je in qset :
        mdict  = {}
        member = je.memberid
        mdict['member']    = {'name':"%s %s" % (member.first, member.last), 'id' : "%05d" % (member.memberid)}
        mdict['entrydate'] = "%s" % (je.entrydate.strftime('%A %B %d, %Y'))
        mdict['subject']   = "%s" % (je.entrytype)
        mdict['comment']   = "%s" % (je.comment)
        elist.append(mdict)
    cdict['entries'] = elist    
    return cdict

# Processing utilities for adding or updating Pets, Tags, and
# Member-Pet relationships. Common code to membercreate and memberactions
# -----------------------------------------------------------------------
def util_badtagonly  (req, member_id, pform, tform) :
    """
    """
    newpet      = Pet()
    newlink     = MemberPet()
    member      = Member.objects.get(pk=member_id)
    newpet.name = pform.cleaned_data.get('pf_name')
    if not(pform.cleaned_data.has_key('pf_desc')) or len(pform.cleaned_data.get('pf_desc')) == 0 :
        newpet.description = 'None given.'
    else :
        newpet.description = pform.cleaned_data.get('pf_desc')
    newpet.save()
    newlink.member   = member
    newlink.pet      = newpet
    newlink.save()
    return (member, newpet, None, newlink)

# -----------------------------------------------------------------------
def util_emptyform   (req, member_id, pform, tform) :
    """
    """
    pass

# -----------------------------------------------------------------------
def util_registerpet (req, member_id, pform, tform) :
    """
    """
    newpet      = Pet()
    newtag      = DogTag()
    newlink     = MemberPet()
    member      = get_object_or_404(Member, pk=member_id)
    newpet.name = pform.cleaned_data.get('pf_name')

    if not(pform.cleaned_data.has_key('pf_desc')) or len(pform.cleaned_data.get('pf_desc')) == 0 :
        newpet.description = 'None given.'
    else :
        newpet.description = pform.cleaned_data.get('pf_desc')
    newpet.save()
    newtag.petid     = newpet
    newtag.tagnumber = tform.cleaned_data.get('ta_number')
    newtag.tagstatus = 'Assigned'
    newtag.save()
    newlink.member   = member
    newlink.pet      = newpet
    newlink.save()
    return (member, newpet, newtag, newlink)


# -----------------------------------------------------------------------
def util_setmemberpreferences(req, member_id) :
    """
    Preferences are presently binary flags that turn on/off a fixed (at the
    db level) number of standard preferences. As of 08-Feb-2011 this fixed
    list of preferences has two elements: 1. Getting the newsletter via U. S.
    mail and 2. Getting the broadcast email. 
    """
    # The preference the user wishes to alter will be present as a keyword
    # in the POST mapping; it's value in that mapping will be a one element
    # list containing either the string 'Add' or 'Remove'
    
    def addpref (p, plst) :
        """
        Add item 'p' to preference list 'plst' only if it is not already present
        use set intermediary to cull duplicate additions
        """
        pset = set(plst)
        pset.add(p)
        return list(pset)
    
    def removepref (p, plst) :
        """
        Remove item 'p' from preference list 'plst' only if it is already present
        with set intermediary, finding the location of p is unnecessary: a set is
        a nonsequential collection of distinct things.
        """
        pset = set(plst)
        pset.discard(p)
        return list(pset)

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

    if len(memberpref.prefs) > 0 : 
        preflst = memberpref.prefs.split(',')
    else :
        preflst = list()
    for tuplet in memberpref.prefclasses :
        if tuplet[0] in req.POST : break
    memberpref.prefs = ",".join({'Add':addpref, 'Remove':removepref}[req.POST[tuplet[0]]](tuplet[0], preflst))    
    memberpref.save()
    return (member, memberpref) 
