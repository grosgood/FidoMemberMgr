#! /usr/bin/python
# ---------------------------------------------------------------------------
# Generate Vistaprint Maillist
# ---------------------------------------------------------------------------
"""
MAKEMAILLIST.PY
Generate Vistaprint Maillist
"""
import sys
import os
import collections
from optparse import OptionParser
os.environ['DJANGO_SETTINGS_MODULE'] = 'fidoonline.settings'
sys.path.append('/media/FireTwo/FidoMembership')
import uno
# ==========================================================================================
def mkfilenameurl(path) :
    """
    string path reference to a file
    return file URL or None if the file could not be located
    """
    lclpath = os.path.abspath(path)
    if(os.path.isfile(lclpath)) :
       return "file://%s" % lclpath
    return None
# ---------------------------------------------------------------------------
def makeOfficeConnection() :
    """
    Start OO office environment, UNO bridge, and get a desktop in that environment
    """
    import officeconnect
    return officeconnect.OODesktop()
# ---------------------------------------------------------------------------
def fetchMemberAddresses() :
    """
    foreach known mail address, fetch the one, two, three... Fido Members associated with the address.
    return as a list of dictionaries
    """
    from fidoonline.membermanage.models import MailAddress, Member

    mal = MailAddress.objects.all()
    dictlist  = []
    for ma in mal :
        residents = Member.objects.filter(mailadr__exact = ma.adrid)
        if residents.count() :
            reslist = []
            for oneres in residents :
                reslist.append({'first': "%s" % (oneres.first), 'last': "%s" % (oneres.last), 'memberid': "%05d" % (oneres.memberid)})
            dictlist.append({'residents': reslist, 'street' : ma.street, 'aptnum': ma.aptnum, 'city' : ma.city, 'state' : ma.state, 'zipcode' : "%s-%s" % (ma.zipcode, ma.zipext)})      
    return dictlist
# ---------------------------------------------------------------------------
def combineNames(namelist) :
    if   len(namelist) == 0 :
        return ('', '', '', '', '', '')
    elif len(namelist) == 1 :
        return ('', namelist[0]['first'], '', namelist[0]['last'], '', '')
    else :
        if namelist[0]['last'] == namelist[1]['last'] :
            return ('', '%s & %s' % (namelist[0]['first'], namelist[1]['first']), '', namelist[0]['last'], '', '')
        else :
            return ('', '%s %s' % (namelist[0]['first'], namelist[0]['last']), '&', '%s %s' % (namelist[1]['first'], namelist[1]['last']), '', '')
# ---------------------------------------------------------------------------
def populateOneRow(indx, sheet, sz, dict) :
    """
    """
    colors  = ('ccffee', '99ffdd')
    rc = sheet.getCellRangeByPosition(0, indx + 1, sz - 1, indx + 1)
    ds = combineNames(dict['residents']) + ('', dict['street'], dict['aptnum'], dict['city'], dict['state'], dict['zipcode'])
    rc.setDataArray((ds,))
    rc.setPropertyValue("CellBackColor", int(colors[indx % 2], 16))
# ---------------------------------------------------------------------------
def populateSpread(sprd, dlist) :
    """
    """
    sheet = sprd.getSheets().getByIndex(0)
    vphdr = ('Salutation', 'First name', 'Middle', 'Last Name', 'Suffix', 'Title', 'Company', 'Address Line 1', 'Address Line 2', 'City', 'State', 'Zip+4')
    sz  = len(vphdr)
    hc  = sheet.getCellRangeByPosition(0, 0, sz - 1, 0)
    hc.setDataArray((vphdr,))
    hc.setPropertyValue("CellBackColor", int("9999ff", 16))
    hc.setPropertyValue("CharColor",     int("e6e6ff", 16))
    hc.setPropertyValue("CharWeight",    200)
    for indx in range(0, len(dlist)) :
        populateOneRow(indx, sheet, sz, dlist[indx])
    print ('Done')
# ---------------------------------------------------------------------------
def main () :
    """
    entry point
    """
    from com.sun.star.beans import PropertyValue
    
    hideme = PropertyValue()
    hideme.Name  = "Hidden"
    hideme.Value = True
    parser = OptionParser()
    parser.add_option("-s", "--spreadsheet", action="store",      type="string", dest="spread",   help="Partial path and name of Spreadsheet for Vistaprint maillist data", metavar="SPREAD", default="")
    parser.add_option("-v", "--visible",     action="store_true",                dest="visible",  help="Bring the document to the forground; normally the report is written as a hidden document.", metavar="VISIBLE", default=False)
    (options, args) = parser.parse_args()

    # set up the spread
    memberspread = mkfilenameurl(options.spread)
    if not(memberspread) :
        sys.exit("Could not locate '%s'" % options.spread)

    #Start OOffice server.
    ofc  = makeOfficeConnection()
    dsk  = ofc.getDesk()
    if options.visible :
        sprd = dsk.loadComponentFromURL(memberspread, "_default", 0, ())
    else :
        sprd = dsk.loadComponentFromURL(memberspread, "_default", 0, (hideme,))
    populateSpread(sprd, fetchMemberAddresses())    
# ==========================================================================================
if __name__ == '__main__' :
    main()
