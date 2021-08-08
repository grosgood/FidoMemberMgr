
"""
memberviews.py
HTTP request object processors for the membermanage application that generate detail documents about member records.
"""
from django.contrib.auth.decorators     import login_required
from django.core.context_processors     import csrf
from django.core.urlresolvers           import reverse
from django.http                        import HttpResponseRedirect, HttpResponse
from django.shortcuts                   import render_to_response, get_object_or_404
from fidoonline.membermanage.memberutil import find_member_submit, mkjournallist, mkmembercontactdictionary, mkmemberdueslist, mkmemberpetlist, mkmemberpicker, mkmemberpreferences, mknonmemberdictionary, mknonmemberdueslist, mknonmemberjournallist, mknonmemberpetlist, mknonmemberpreferences 
from fidoonline.membermanage.models     import Member
# import pydb

# -------------------------------------------------------------------------------------
def launchquadrant(req, member_id, tablegenerator, nomembergenerator, displaytemplate, target=None) :
    """
    This utility executes a generic wrapper slung around the table
    generators, targets and templates that Django employs to project an
    initial quadrant display, employing the context dictionary and
    display template to build a particular view, or data slice of the
    member database.

    That slice, whatever it may be, arises from the particular choice
    of a table generator routine. In the case that the member ID is
    not assigned, a second 'non member' table generator furnishes a
    default display. These table generator routines live in
    fidoonline.membermanage.memberutil and deal with the specifics of
    context dictionary construction.

    The displaytemplate is a reference to a file written in Django
    template syntax.  The standard for quadrants is
    'membermanage/membertable.html' and most table generators have
    been written to furnish a context dictionary to populate this
    particular template.
    
    A submit button for further actions is (usually) a part of the web
    page that Django concocts from the generator/display template
    pair. If that submission requires a data entry form of some sort,
    then TARGET should point to a dotted namespace reference of the
    Python function that underlies the 'action URL' furnished to the
    <FORM> tag's ACTION attribute. The file membermanage/urls.py
    establishes the correspondence between this URL and the Python
    function; we choose not to hardwire URL's here; we employ Django's
    reverse() utility to make use of the map that membermanage/urls.py
    provides and Django will choose the appropriate URL - unless (of
    course) urls.py is incomplete or incorrect.
    """
    c = csrf(req)
    try :
        member = Member.objects.get(pk=member_id)
    except Member.DoesNotExist :
        cntxdict = {'member' : nomembergenerator(member_id)}
        cntxdict.update(c)
        return render_to_response(displaytemplate, cntxdict)
    if target :
        cntxdict = {'member' : tablegenerator(member, reverse(target, args=[member_id]))}
    else :    
        cntxdict = {'member' : tablegenerator(member)}
    cntxdict.update(c)
    return render_to_response(displaytemplate, cntxdict)
# -------------------------------------------------------------------------------------Fido47Friends!
@login_required
def detailmembercontact (req, member_id) :
    """
    Render out member's name, address, email and telephone number
    """
    return launchquadrant(req, member_id, mkmembercontactdictionary, mknonmemberdictionary, 'membermanage/membercontact.html')
# -------------------------------------------------------------------------------------
@login_required
def detailmemberdues (req, member_id) :
    """
    Render out dues payment listing of the member
    """
    return launchquadrant(req, member_id,  mkmemberdueslist, mknonmemberdueslist, 'membermanage/membertable.html', 'fidoonline.membermanage.memberactions.recordduespayment')
# -------------------------------------------------------------------------------------
@login_required
def detailmemberpets (req, member_id) :
    """
    Render out list of pets, with descriptions, tags, and individual edit buttons.
    """
    return launchquadrant(req, member_id, mkmemberpetlist, mknonmemberpetlist, 'membermanage/membertable.html', 'fidoonline.membermanage.memberactions.recordpet')
# -------------------------------------------------------------------------------------
@login_required
def detailmemberjournal (req, member_id) :
    """
    Render out the member's Journal records. Furnish a text box for ad-hoc Journal entries
    """
    return launchquadrant(req, member_id, mkjournallist, mknonmemberjournallist, 'membermanage/membertable.html', 'fidoonline.membermanage.memberactions.addjournalrecord')
# -------------------------------------------------------------------------------------
@login_required
def detailmemberpreferences (req, member_id) :
    """
    Render out the list of known preferences; furnish a checkbox button
    with each to indicate an enabled preference (such would be checked).
    Editors may dis/enable checkboxes, with server round-trip occuring
    on the submit button - no intermediary edit form is needed.
    Preferences as of this release, 08-Feb-2011, are two:
        1. getting a newsletter by U. S. Mail.
        2. getting Bob Ipcar's broadcast email.
    Need to alter MemberPreference table and allied model to add/change
    preferences ( :( )BIG FIXME - db should only store abstract key-value
    pairs and have no 'knowledge' of what they are. This application stores
    a 'Broadcast Email' key and sets its value to True; the DB only records
    that 'Broadcast Email' is a recognized key. Then preferences can be added
    and taken away by application inserts/deletes to the table; better than
    the current hardwired preference set defined and fixed in MemberPreference
    
    """
    return launchquadrant(req, member_id, mkmemberpreferences, mknonmemberpreferences, 'membermanage/membertable.html', 'fidoonline.membermanage.memberactions.setmemberpreferences' )
# -------------------------------------------------------------------------------------
@login_required
def findmemberbyname(req, bannerflag=False) :
    """
    Member lookup. Initially (i.e. first page load request from the
    browser) offers a Lookup textbox; on subsequent requests, looks
    first for a memberpick string among the POST keys ('MID-' followed
    by a member identifier), and then, failing that, constructs a set
    of submit buttons, one for each member who fits the filter string
    given by the 'lu_search', key in the request POST. On subsequent
    request/response cycles, such buttons originate the 'MID-xxxxx'
    strings that indicate to this handler that the user has picked a
    member for detailing.

    Most of the previous narrative is encapulated in the
    mkmemberpicker utility, which interacts with the Lookup Form
    object. This wrapper to that utility concerns itself with
    responses from any one of the submit buttons forwarded via the
    form during previous request/response cycles.
    """
    def has_member_been_found(req) :
        """
        Should one be found, construct an HTTP redirect response
        to the detail page of the member corresponding to the identifier,
        else, return None, so that the caller may construct a new set of submit
        buttons based upon the current content of the lu_search field
        in the POST request.
        """
        member_id = find_member_submit(req) 
        if member_id :
            return  HttpResponseRedirect( reverse('fidoonline.membermanage.memberviews.detailmemberframeset', args=[member_id]))
    # ---------------------------------------------------------------------------------
    bannerflag = bool(bannerflag == 'True')
    pkresponse = has_member_been_found(req)
    if pkresponse :
        return pkresponse
    cntxdict = csrf(req)
    wizard   = ('Newmember','New Member', 'startWizardWindow', reverse('fidoonline.membermanage.membercreate.makenewrecord'))
    cntxdict.update({'addenda' : mkmemberpicker(req, reverse('fidoonline.membermanage.memberviews.findmemberbyname', args=[str(bannerflag)]), '_parent', jsaction=wizard, banner=bannerflag), 'scriptlist': ['/sitemedia/js/fidositecore.js']})
    return render_to_response('membermanage/membersearch.html', cntxdict)
# -------------------------------------------------------------------------------------
@login_required
def detailmemberframeset (req, member_id) :
    """
    membermanage/urls.py maps the generic member detail URL to this function; it employs a sextet (frmly quintet, hence
    template's name) of inline frames that each contain a slice of the overall presentation of member detail. These are:
        1. (northwest)  :  contact information - member ID, member name, address, telephone number and email.
        2. (northeast)  :  dues payment history
        3. (southwest)  :  pets the member is affiliated with, and links to other members who are 'co-owned' by the pet ;)
        4. (southeast)  :  the journal of various things of note about the member
        5. (bottomleft) :  checkboxes of member preferences.
        6. (bottomright):  search box and chooser to display other members
        
    Those with edit privileges have pages with action submit buttons that initiate various changes that can
    be made to the database. Others will see data tables and no buttons; can look but not play.
    Because iframes are in play, the response page this function constructs will engender the user's browser
    to initiate six more requests for each of the iframe items listed above. 
    """
    bannerflag   = False;
    try :
        member       = Member.objects.get(pk=member_id)
        membername   = ' '.join(str(member).split()[1:])
    except Member.DoesNotExist :
        membername   = ''
        
    detailagents = {
                     'northwestsloturl' : reverse('fidoonline.membermanage.memberviews.detailmembercontact',     args=[member_id]),
                     'northeastsloturl' : reverse('fidoonline.membermanage.memberviews.detailmemberdues',        args=[member_id]),
                     'southwestsloturl' : reverse('fidoonline.membermanage.memberviews.detailmemberpets',        args=[member_id]),       
                     'southeastsloturl' : reverse('fidoonline.membermanage.memberviews.detailmemberjournal',     args=[member_id]),
                     'southsloturl'     : reverse('fidoonline.membermanage.memberviews.detailmemberpreferences', args=[member_id]),  
                     'searchsloturl'    : reverse('fidoonline.membermanage.memberviews.findmemberbyname',        args=[bannerflag])  
                   }
    slotdict = {
                 'crumbline' : ({'label': 'Start Here', 'link': reverse('fidoonline.membermanage.starthereview.start')}, {'label': 'Member Directory', 'link': reverse('fidoonline.membermanage.views.memberlist')}, {'label': membername, 'link': None}),
                 'slots'     : detailagents 
               }
    return render_to_response('membermanage/fivepanelframe.html', slotdict)
