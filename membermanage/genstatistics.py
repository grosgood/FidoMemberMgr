#! `which python`
"""Generators of statistics charts displayed by the FIDO Member Manager."""
import datetime                           as dt
import matplotlib.pyplot                  as plt
import matplotlib.font_manager            as fmgr
import numpy                              as np
import os
import pytz
import sys
APP_PATH                             = os.path.realpath(os.path.dirname(__file__))
app_base, app_name                   = os.path.split(APP_PATH)
project_path, project_name           = os.path.split(app_base)
sys.path.append(project_path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'fidoonline.settings'
from django.contrib.auth.decorators       import login_required
from django.http                          import HttpResponseRedirect, HttpResponse
from django.shortcuts                     import render_to_response, get_object_or_404
from django.template                      import Context, loader
from optparse                             import OptionParser
from fidoonline.membermanage.models       import Dues, EMailAddress, Journal, MailAddress, Member, MemberPet, MemberPreference, Pet, TelNumber 

terms = None    
# ---------------------------------------------------------------------------------
def __getterms() :

    """Return a list of integers, each being a term of a Fido
    member. The integers in this list has a one-to-one correspondence
    with Fido members."""

    return np.array(map(lambda m: m.expiry, Member.objects.all().order_by('memberid')))

# ---------------------------------------------------------------------------------
def __getmediaroot() :
    """Furnishes the directory where chart documentation should be written."""

    from fidoonline.settings import MEDIA_ROOT as picdir

    return os.path.join(picdir, 'charts')

# ---------------------------------------------------------------------------------
def memberSummary(fname='sumpie', height=6.0, width=6.0) :

    """Generates a pie chart depicting the FIDO membership in terms of
    the dues payment classes: 'Active', 'Expiring', 'Expired', or
    'Inactive.' Members pay dues or make a purchase regarded as the
    equivalent to paying dues. If the period from this action to the
    current date is less than two hundred seventy days, the member is
    classed as 'Active', or 'Expiring' if the period is two hundred
    seventy to less than a calendar year, or 'Expired if the period is
    a calendar year to less than four hundred fifty five days, or
    'Inactive' if the period is four hundred fifty five days or more.

     *fname*: string - the name to which the pie chart image will be
     written; defaults to 'sumpie.png'. The extension commonly sets
     the graphic format; the availability of such depends on the
     rendering backends compiled into the underlying matplotlib
     package. Global MEDIA_ROOT establishes the file's directory.
 
     *height*: of the graph in relative figure units. DPI, a
     matplotlib configuration value, assigns a count of physical
     pixels to this unit.

     *width*: of the graph in relative figure units (see 'height')."""

    global terms
    from fidoonline.settings import MEDIA_ROOT as picdir

    if terms == None :
        terms = __getterms()

    picfile   = os.path.join(picdir, 'charts', '{0}.png'.format(fname))
    thmbfile  = os.path.join(picdir, 'charts', '{0}_thumb.png'.format(fname))
    memcount  = len(terms)
    active    = len(terms[(terms > 90)])
    expiring  = len(terms[(terms > 0) & (terms <= 90)]) 
    expired   = len(terms[(terms > -90) & (terms <= 0)])
    inactive  = len(terms[(terms <= -90)])
    figure    = plt.figure(num=1, figsize=(width, height))
    now       = dt.datetime.now(tz=pytz.timezone('America/New_York'))
    plt.suptitle("FIDO Membership")
    plt.title("%s" % (now.strftime(format='%B %d, %Y %I:%M %p %Z')))
    artary    = plt.pie(np.array([inactive, expired, expiring, active], np.float32), labels=('Inactive: (%4d)' % (inactive), 'Expired: (%4d)' % (expired), 'Expiring: (%4d)' % (expiring), 'Active: (%4d)' % (active),), colors=('#e04000', '#e08000', '#e0e000', '#00e040'), autopct="%4.2f%%")
    axes      = plt.gca()
    axes.set_aspect('equal')
    artary[2][0].set_fontsize('x-small')
    artary[2][1].set_fontsize('x-small')
    artary[2][2].set_fontsize('x-small')
    artary[2][3].set_fontsize('x-small')
    artlgn = plt.text(0.5, -1.5, 'Member Total: %4d' % (memcount)) 
    figure.savefig(picfile, facecolor='#cddbb8', linecolor='#cddbb8', dpi=100)
    figure.savefig(thmbfile, facecolor='#cddbb8', linecolor='#cddbb8', dpi=36)
    plt.close(1)
    return os.path.exists(picfile) and os.path.exists(thmbfile) 

# ---------------------------------------------------------------------------------
def memberCohort(fname='cohort', cdays=90, majorinterval=4, height=6.0) :
    """Sort members into cohorts, defaulting to 90 days, based on the
    period in days to their membership term expiration, for positive
    cohorts, or days since their terms expired, for negative
    cohorts. Depict the cohorts as elements of a bar chart. Red
    elements depict inactive members, green active. For 90 day
    cohorts, the default, a pale green and pale red bar depicts
    expiring and expired member classes. Cohorts are with respect to
    the date when the chart is compiled and constitutes the zero
    reference day.

    *fname*: string - the name to which the pie chart image will be
    written. Defaults to 'cohorts.png.' The extension commonly sets
    the graphic format; this, in turn, depends on the available
    rendering backends compiled into the underlying matplotlib
    package. Global MEDIA_ROOT establishes the file's directory.

    *cdays*: integer - the duration in days of one cohort, defaults to
    ninety days.
 
    *height*: integer - of the graph in relative figure units; defaults
    to 6.0 units. DPI, a matplotlib configuration value, assigns a
    count of physical pixels to this unit."""

    
    global terms
    from fidoonline.settings import MEDIA_ROOT as picdir

    if terms == None :
        terms = __getterms()

    picfile     = os.path.join(picdir, 'charts', '{0}.png'.format(fname))
    thmbfile    = os.path.join(picdir, 'charts', '{0}_thumb.png'.format(fname))
    lcount      = np.int32(np.floor(terms.min()/float(cdays)))
    rcount      = np.int32(np.ceil(terms.max()/float(cdays)))
    ccount      = rcount - lcount
    now         = dt.datetime.now(tz=pytz.timezone('America/New_York'))
    nowcindex   = -(lcount + 1)
    # Count of members in bdat[x] constitutes the cohort between dates legends[x-1] & legends[x] 
    bdat        = map(lambda i: len(terms[(cdays*(i + lcount) < terms) & (terms < cdays*(i + lcount + 1))]), xrange(ccount))
    legends     = map(lambda i: (now + dt.timedelta(days=int(cdays*(i + lcount + 1)))).strftime(format='%d-%b-%y'), xrange(ccount))
    fig         = plt.figure(num=1, figsize=(0.3*ccount, height))
    plt.suptitle("FIDO Membership - 90 Day Cohort Distribution")
    plt.title("%s" % (now.strftime(format='%B %d, %Y %I:%M %p %Z')))
    bars        = plt.bar(np.array(range(0, ccount), np.int32), bdat, color='#e04000', linewidth=1)
    bars[nowcindex].set_facecolor('#e08000')
    bars[nowcindex + 1].set_facecolor('#e0e000')
    map(lambda i: bars[i].set_facecolor('#00d020'), range(nowcindex + 2, ccount))
    plt.grid(True)
    ax          = fig.axes[0]
    ax.set_xbound((0, ccount))
    tik_artists = ax.set_xticks(np.array(range(0, ccount), np.int32))
    #Mark every 4th cohort from zero day (the date of the chart) - mark zero day specially 
    cnt, off = divmod(nowcindex, majorinterval)
    map(lambda l: l.get_children()[2].set(linestyle='-', color="#9090f8", linewidth=1), ax.xaxis.get_major_ticks()[off::majorinterval])
    ax.xaxis.get_major_ticks()[nowcindex].get_children()[2].set(linestyle='-', color="#e04000", linewidth=2)
    #Similar markings on the text legends too
    lab_artists = ax.set_xticklabels(legends)
    map(lambda a: a.set(fontsize=8.0, rotation=45.0, horizontalalignment='center'), lab_artists)
    map(lambda a: a.set(weight='bold'), lab_artists[off::majorinterval])
    lab_artists[nowcindex].set(color="#e04000")
    #Member count in each cohort
    mcntp = fmgr.FontProperties(style='normal', variant='normal', weight='normal', stretch='normal', size='x-small')
    for b in bars:
        height = b.get_height()
        ax.text(b.get_x() + b.get_width()/2., 1.2 + height, '%d'%int(height), ha='center', va='bottom', fontproperties=mcntp)
    fig.savefig(picfile, facecolor='#cddbb8', linecolor='#cddbb8', dpi=100)
    fig.savefig(thmbfile, facecolor='#cddbb8', linecolor='#cddbb8', dpi=36)
    plt.close(1)
    return os.path.exists(picfile) and os.path.exists(thmbfile) 
    
# ---------------------------------------------------------------------------------
if __name__ == '__main__' :

    everybody = Member.objects.all()
    terms     = np.array(map(lambda m: m.expiry, everybody), np.int32)
    memberSummary(width=6.0, height=6.0)
    memberCohort(cdays=90)
    print 'Done'
