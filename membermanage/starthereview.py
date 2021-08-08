"""
starthereview.py
The FIDO Member Manager top level page 
"""
from django import forms
from django.db import transaction
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.core.context_processors     import csrf
from django.core.urlresolvers           import reverse
from django.forms.util                  import ErrorList
from django.contrib.auth.decorators     import login_required
from fidoonline.membermanage.memberutil import find_member_submit, mkjournalentrydisplaytable, mkmembercontactdictionary, mkmemberdueslist, mkmemberpetlist, mkmemberpicker, mkmemberpreferences, mknonmemberdictionary, mknonmemberdueslist, mknonmemberjournallist, mknonmemberpetlist, mknonmemberpreferences 
from fidoonline.membermanage.models     import Member, MemberPet, Pet, DogTag, EMailAddress, TelNumber 
from fidoonline.membermanage.forms      import Lookup
from fidoonline.membermanage.views      import memberlist
from fidoonline.membermanage.petviews   import listpets
# import pydb
# 2020-December-21 Can't do member statistics
# -------------------------------------------------------------------------------------
@login_required
def start (req) :
    """
    Furnishes the top level page for the FIDO Member Manager
    Uses directory template
    """
    import datetime as dt
    
    wizard   = ('Newmember','New Member', 'startWizardWindow', reverse('fidoonline.membermanage.membercreate.makenewrecord'))
    homedict = {
                 'addenda'      : mkmemberpicker(req, reverse('fidoonline.membermanage.memberviews.findmemberbyname', args=[True]), 'memberfinder', jsaction=wizard, banner=False),
                 'colcount'     : 2, 
                 'crumbline'    : ({'label': 'Start Here', 'link': None},),
                 'directoryset' : (
                                    (
                                      {'name': 'Member Directory',   'location': reverse('fidoonline.membermanage.views.memberlist')},
                                      {'name': 'Pet Directory',      'location': reverse('fidoonline.membermanage.petviews.listpets')},
                                      {'name': 'Tag List Directory', 'location': reverse('fidoonline.membermanage.petviews.listtags')},
#                                     {'name': 'Member Statistics',  'location': reverse('fidoonline.membermanage.statistics.summary')},
                                    )
                                  ),
                 'directtitle'  : "Available Directories",
                 'j_title'      : "Updates",
                 'j_summary'    : "Changes to membership records in the last forty five days.",
                 'jentries'     : mkjournalentrydisplaytable({'basedate': dt.datetime.now() - dt.timedelta(days=45), 'duration': 45}),
                 'pagetitle'    : "FIDO Membership Matters",
                 'scriptlist'   : ['/sitemedia/js/fidositecore.js'],
                 'search_title' : "Find",  
                 'window_title' : "FIDO Membership Management Site"
               }
    homedict.update(csrf(req))

    return render_to_response('membermanage/directory.html', homedict)
