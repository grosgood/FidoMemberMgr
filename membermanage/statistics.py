"""
statistics.py
HTTP request object processors for the membermanage application which furnish a set of graphs.
"""
import datetime                           as dt
import matplotlib.pyplot                  as plt
import numpy                              as np
import os
import pytz
import re
import sys
from django.contrib.auth.decorators       import login_required
from django.http                          import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers             import reverse
from django.shortcuts                     import render_to_response, get_object_or_404
from django.template                      import Context, loader
from fidoonline.membermanage.models       import DogTag, EMailAddress, MailAddress, Member, MemberPet, Pet, TelNumber

# import pydb

# -------------------------------------------------------------------------------------
@login_required
def summary(req) :
    """
    Build a directory of available charts of member activity (currently stubbed)
    """
    from fidoonline.settings import MEDIA_URL as staturl
    from fidoonline.settings import MEDIA_ROOT as statroot

    statpak={'pgtitle': 'Vital Statistics'}
    statpak['crumbline'] = ({'label': 'Start Here', 'link': reverse('fidoonline.membermanage.starthereview.start')}, {'label': 'Vital Statistics', 'link': None},)    

    # Get the assets.
    # Form: foo.png       - a chart called 'foo'
    #       foo_thumb.png - a tiny version of chart 'foo'
    #       foo_doc.txt   - documentation about chart 'foo'
    chartbase = "{0}/charts".format(statroot)
    charturl  = "{0}charts".format(staturl)
    charts    = os.listdir(chartbase)
    if len(charts) > 0 :
        chartlist  = []
        for base in map(lambda r: r[0], filter(lambda s: len(s) > 1 and s[1] == 'thumb', map(lambda s: s.split('_'), map(lambda t: t.split('.')[0], charts)))) :
            try :
                docfp   = open(os.path.join(chartbase, '{0}_doc.txt'.format(base)), 'rb')
                htxt    = docfp.read()
                docfp.close()
                chartlist.append({'image': '{0}.png'.format(base), 'thumb': '{0}_thumb.png'.format(base), 'doc': htxt, 'name' : base })
            except IOError :
                continue
        statpak['charts']    = chartlist
        statpak['charturl']  = charturl
    else :
        statpak['statusmsg'] = 'There are no statistical charts. Is fidostatmaker installed?'

    return render_to_response('membermanage/statistics.html', statpak)
