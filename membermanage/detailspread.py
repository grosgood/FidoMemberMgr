#! /usr/bin/python
# ---------------------------------------------------------------------------
# Generate User Detail
# ---------------------------------------------------------------------------
"""
Detailspread.py
Make a spreadsheet containing summary and detail for each FIDO member
Depends on OpenOfficeOrg Unified Network Objects
Depends on django membermanage models, fidoonline.membermanage.models, fidoonline.membermanage.reviewmodels 
"""
import sys
import os
import collections
from optparse import OptionParser
os.environ['DJANGO_SETTINGS_MODULE'] = 'fidoonline.settings'
sys.path.append('/run/media/gosgood/FireTwo/FidoMembership')
from fidoonline.membermanage.models import Dues, EMailAddress, Journal, MailAddress, Member, MemberPet, MemberPreference, Pet, TelNumber 
from fidoonline.membermanage.reviewmodels import DuesReview 
from django.db.models import Max
import uno
statushistogram = collections.defaultdict(int)
sheetallocations = None
memberindexdict  = {
                    'MemberDirectory': {
                                         'visited'  : 0,
                                         'header'   : ('Member ID', 'FIDO Member', 'Street', 'City', 'State', 'Zip Code', 'Telephone', 'EMail', 'Contact Status'),
                                         'populate' : lambda m: (
                                                                  "%05d"   % (m.memberid),
                                                                  "%s %s"  % (m.first, m.last),
                                                                  m.contactdict['address'],
                                                                  m.contactdict['city'],
                                                                  m.contactdict['state'],
                                                                  m.contactdict['zipcode'],
                                                                  m.contactdict['telnumber'],
                                                                  m.contactdict['emailadr'],
                                                                  m.contactdict['contactstatus']
                                                                )
                                       },
                    'DuesReview':      {
                                         'visited'  : 0,
                                         'header'   : ('Member ID', 'FIDO Member', 'Term Beginning', 'Term Ending', 'Latest Payment', 'Total Pd', 'No. of Payments', 'Days Left (-Since Expiry)'),
                                         'populate' : lambda m: (
                                                                  "%05d"   % (m.memberid),
                                                                  "%s %s"  % (m.first, m.last),
                                                                  m.duesreview.begin.strftime('%B %d, %Y'),
                                                                  m.duesreview.end.strftime('%B %d, %Y'),
                                                                  m.dues_set.aggregate(Max('paydate'))['paydate__max'].strftime('%B %d, %Y'),
                                                                  "$%5.2f" % m.duesreview.totaldues,
                                                                  "%d" % m.dues_set.count(),
                                                                  m.duesreview.expiry
                                                                )
                                       }
                   }
# ---------------------------------------------------------------------------
def makeOfficeConnection() :
    """
    Start OO office environment, UNO bridge, and get a desktop in that environment
    """
    import officeconnect
    return officeconnect.OODesktop()
# ---------------------------------------------------------------------------
def formatSpread(sprd) :
    """
    sprd: Open Office UNO for the spreadsheet
    Paginate spreadsheet.
    """
    import string
    # Sheet names as tabs
    tabs= memberindexdict.keys()
    for t in string.uppercase :
        tabs.append(t)

    sheets = sprd.getSheets()
    for tabname in reversed(tabs) :
        sheets.insertNewByName(tabname, 0)
# ---------------------------------------------------------------------------
def startRange(sheet, key, lines) :
    """
    sheet: An Open Office UNO representing a spreadsheet of cells
    (com.sun.star.sheet.XSpreadsheet)
    key:   Letter identifying one of the member detail sheets
    lines: rows required for member detail.
    Returns: com.sun.star.table.XCellRange
    """
    import string
    global sheetallocations
    
    # Initial setup. Allocation of rows per lettered sheet.
    if sheetallocations == None :
        tabs = []
        for t in string.uppercase :
            tabs.append((t, -1))
        sheetallocations = dict(tuple(tabs))
    try :    
        if sheetallocations[key] + lines > 65355 :
            # No available room. We've filled nearly 65,356 rows. How verbose.
            raise OverflowError ("Sheet %s filled to capacity." % key)
        else :
            if sheetallocations[key] < 0 :
                # Sheet is empty. Set column widths
                sheet.getColumns().getByIndex(0).setPropertyValue("Width", 5060)
                sheet.getColumns().getByIndex(1).setPropertyValue("Width", 14000)

            index = sheetallocations[key] + 1
            sheetallocations[key] += lines
            return sheet.getCellRangeByPosition(0, index, 1, index + lines - 1)
    except KeyError :
        print "WTF?"

# ---------------------------------------------------------------------------
def detailMember(m, sprd) :
    """
    Acquire drill down detail about member from the database and
    compose an entry about the person in the particular spreadsheet
    identified by the first letter of his last name.
    
    m:    django Member object
    sprd: An Open Office unified network object (UNO) representing a
          spread sheet document
    """
    from com.sun.star.table.CellHoriJustify import STANDARD as CH_STANDARD
    from com.sun.star.table.CellHoriJustify import LEFT     as CH_LEFT
    from com.sun.star.table.CellHoriJustify import RIGHT    as CH_RIGHT
    from com.sun.star.table.CellHoriJustify import CENTER   as CH_CENTER
    from com.sun.star.table.CellHoriJustify import BLOCK    as CH_BLOCK
    from com.sun.star.table.CellHoriJustify import REPEAT   as CH_REPEAT
    from com.sun.star.table.CellVertJustify import STANDARD as CV_STANDARD    
    from com.sun.star.table.CellVertJustify import TOP      as CV_TOP   
    from com.sun.star.table.CellVertJustify import CENTER   as CV_CENTER    
    from com.sun.star.table.CellVertJustify import BOTTOM   as CV_BOTTOM
    import datetime

    dataset = []
    # ---------------------------------------------------------------------------
    def mkname(m) :
        """
        Format salutation, first name, middle name, lastname
        return as string
        m: django fido member instance
        """
        dys = m.duesreview.expiry
        s = f = mid = l = stat = "" 
        if len(m.salute): s   = "%s "  % m.salute  
        if len(m.first) : f   = "%s "  % m.first 
        if len(m.middle): mid = "%s "  % m.middle  
        if len(m.last)  : l   = "%s"   % m.last
        
        if   dys > 90  : stat = 'Active' 
        elif dys >  0  : stat = 'Expiring'
        elif dys >-90  : stat = 'Expired'
        else           : stat = 'Inactive'
        
        return s + f + mid + l + " - " + stat
    # ---------------------------------------------------------------------------
    def checkContactStatus(m) :
        """
        Assemble mail address, telephone, and email presentation strings and
        capture contact status while about the task.
        m: django fido member instance
        """
        global statushistogram
        statuskey = 0
        if m.mailadr           == None or \
           m.mailadr.street    == None or \
           m.mailadr.city      == None or \
           m.mailadr.state     == None or \
           m.mailadr.zipcode   == None or \
           m.mailadr.zipext    == None :
            statuskey = statuskey + 1
            company = address = city = state = zipcode = ''
        else :
            if not (m.mailadr.company == None or len(m.mailadr.company) == 0):
                company = m.mailadr.company
            else :
                company = ''
            address     = "%s %s" % (m.mailadr.street, m.mailadr.aptnum)
            city        = m.mailadr.city
            state       = m.mailadr.state
            zipcode     = "%s-%s" % (m.mailadr.zipcode, m.mailadr.zipext)
        statuskey *= 2 
        if m.telnumber         == None or \
           m.telnumber.area    == None or \
           m.telnumber.exch    == None or \
           m.telnumber.number  == None :
            statuskey += 1
            telnumber = ""
        else :
            telnumber =  "%03d-%03d-%04d" % (m.telnumber.area, m.telnumber.exch, m.telnumber.number)
            if not (m.telnumber.ext == None or m.telnumber.ext == 0) :
                telnumber += "ext: %d" % m.telnumber.ext
        statuskey *= 2
        if m.emailadr          == None or \
           m.emailadr.domain   == None or \
           m.emailadr.name     == None :
            statuskey += 1
            emailadr = ""
        else :
            emailadr ="%s@%s" % (m.emailadr.name, m.emailadr.domain)
        contactstatus = ['Good', 'No Email', 'No Telephone', 'Only US Mail', 'No US Mail', 'Only Telephone', 'Only Email', 'Lost All Contact'][statuskey]
        statushistogram[contactstatus] += 1
        m.contactdict = {'company': company, 'address': address, 'city': city, 'state': state, 'zipcode': zipcode, 'telnumber': telnumber, 'emailadr': emailadr, 'contactstatus': contactstatus}
    # ---------------------------------------------------------------------------
    def xpdy (dys) :
        """
        Choose color based on expiration status, return as rgb hex string
        dys: days `til expiration. If negative, days since expiration
        """
        rdict = {'active' :'afe092', 'expiring':'e1e079', 'expired':'e8c979', 'inactive':'ff8c47'}
        if   dys > 90  : return rdict['active']
        elif dys >  0  : return rdict['expiring']
        elif dys >-90  : return rdict['expired']
        else           : return rdict['inactive']

    # Sheet to post member detail is named by the first letter of the last name
    sheet = sprd.getSheets().getByName(m.last[0])
    # Member
    h_10 = len(dataset)
    dataset.append((str(m.memberid), "%s" % mkname(m)))

    # Contact
    h_20 = len(dataset)
    checkContactStatus(m)
    dataset.append(("Contact Status", m.contactdict['contactstatus']))
    if len(m.contactdict['company'])   : dataset.append(("Company:", m.contactdict['company']))
    if len(m.contactdict['address'])   : dataset.append(("Street Address:", m.contactdict['address']))    
    if len(m.contactdict['city']) and len(m.contactdict['state']) and len(m.contactdict['zipcode'])  : dataset.append(("", "%s, %s %s" % (m.contactdict['city'], m.contactdict['state'], m.contactdict['zipcode'])))
    if len(m.contactdict['telnumber']) : dataset.append(("Telephone:", m.contactdict['telnumber']))
    if len(m.contactdict['emailadr'])  : dataset.append(("Email:", m.contactdict['emailadr']))

    # Preferences
    h_205  = len(dataset)
    if m.memberpreference :
        dataset.append(("Preferences:", m.memberpreference.prefs))
    else :
        dataset.append(("Preferences:", 'NONE REGISTERED!'))

    # Pets
    h_21 = len(dataset)
    dataset.append(("Pets:", ""))
    for pet in m.pet_set.iterator() :
        dataset.append(("Name", "%s" % (pet.name)))
        dataset.append(("Description", "%s" % (pet.description)))

    # Dues
    h_22 = len(dataset)
    dataset.append(("FIDO Contributions:", ""))
    for d in m.dues_set.iterator() :
        dataset.append(('* %s' % (d.paydate.strftime('%B %d, %Y')), "$%5.2f - %s" % (d.payamount, d.paytype)))

    # Expiry
    h_23 = len(dataset)
    dataset.append(("Expiry:", ""))
    dys = m.duesreview.expiry

    if dys < 0 :
        dataset.append(("Inactive for:", "%d days as of %s " % (-dys, datetime.datetime.now().strftime('%B %d, %Y'))))
    else :
        dataset.append(("Active for:", "%d more days as of %s " % (dys, datetime.datetime.now().strftime('%B %d, %Y'))))
        
    # Journal
    h_24 = len(dataset)
    dataset.append(("Database Journal:", ""))
    for je in m.journal_set.iterator() :
        dataset.append((je.entrytype, "%s: %s" % (je.entrydate.strftime('%B %d, %Y'), je.comment)))
            
    # Post to spreadsheet and beautify.
    cells = startRange(sheet, m.last[0], len(dataset))
    
    # crosslinkurl
    m.detailrange = cells.queryIntersection(cells.getRangeAddress()).getRangeAddressesAsString()
    
    cells.setPropertyValue("CellBackColor", int('e6e6ff', 16))
    cells.setPropertyValue("HoriJustify", CH_LEFT)
    cells.setPropertyValue("VertJustify", CV_TOP)
    cells.setPropertyValue("IsTextWrapped", True)
    cells.getCellRangeByPosition(0, 0, 0, len(dataset) - 1).setPropertyValue("CellBackColor", int('c0e0f8', 16))
    cells.getCellRangeByPosition(0, h_10, 1, h_10).setPropertyValue("CellBackColor", int(xpdy(dys), 16))
    cells.getCellRangeByPosition(0, h_20, 1, h_20).setPropertyValue("CellBackColor", int('9999ff', 16))
    cells.getCellRangeByPosition(0, h_205, 1, h_205).setPropertyValue("CellBackColor", int('9999ff', 16))
    cells.getCellRangeByPosition(0, h_21, 1, h_21).setPropertyValue("CellBackColor", int('9999ff', 16))
    cells.getCellRangeByPosition(0, h_22, 1, h_22).setPropertyValue("CellBackColor", int('9999ff', 16))
    cells.getCellRangeByPosition(0, h_23, 1, h_23).setPropertyValue("CellBackColor", int('9999ff', 16))
    cells.getCellRangeByPosition(0, h_24, 1, h_24).setPropertyValue("CellBackColor", int('9999ff', 16))
    cells.setFormulaArray(tuple(dataset))
    cells.getCellRangeByPosition(0, h_10, 1, h_10).setPropertyValue("CharHeight",  14.0)
    cells.getCellRangeByPosition(0, h_10, 1, h_10).setPropertyValue("CharWeight", 200.0)
    cells.getCellRangeByPosition(0, h_20, 1, h_20).setPropertyValue("CharWeight", 200.0)
    cells.getCellRangeByPosition(0, h_205, 1, h_205).setPropertyValue("CharWeight", 200.0)
    cells.getCellRangeByPosition(0, h_21, 1, h_21).setPropertyValue("CharWeight", 200.0)
    cells.getCellRangeByPosition(0, h_22, 1, h_22).setPropertyValue("CharWeight", 200.0)
    cells.getCellRangeByPosition(0, h_23, 1, h_23).setPropertyValue("CharWeight", 200.0)
    cells.getCellRangeByPosition(0, h_24, 1, h_24).setPropertyValue("CharWeight", 200.0)
# ---------------------------------------------------------------------------
def makeDirectory(m, sprd, sheetname) :
   """
   Make a one line report on a member for either the Member directory
   or Dues Review page.
    m:         django Member object
    sprd:      An Open Office unified network object (UNO) representing a
               spread sheet document
    sheetname: string indicating which page to insert the one liner
   """
   colors  = ('ffeecc', 'ffdd99', 'e6e6ff', 'cce6ff')
   sheet   = sprd.getSheets().getByName(sheetname)
   if memberindexdict[sheetname]['visited'] == 0 : #Make header
      ds  = memberindexdict[sheetname]['header']
      hc  = sheet.getCellRangeByPosition(0, 0, len(ds) - 1, 0)
      hc.setDataArray((ds,))
      hc.setPropertyValue("CellBackColor", int("9999ff", 16))
      hc.setPropertyValue("CharColor",     int("e6e6ff", 16))
      hc.setPropertyValue("CharWeight",    200)
      memberindexdict[sheetname]['visited'] = 1
   ds = memberindexdict[sheetname]['populate'](m)
   rc = sheet.getCellRangeByPosition(0, memberindexdict[sheetname]['visited'], len(ds) - 1, memberindexdict[sheetname]['visited'])
   rc.setFormulaArray((ds,))
   rc.setPropertyValue("CellBackColor", int(colors[memberindexdict[sheetname]['visited'] % 2], 16))
   rc.getCellRangeByPosition(0, 0, 0, 0).setPropertyValue("CellBackColor", int(colors[2 + memberindexdict[sheetname]['visited'] % 2], 16))
   cell = rc.getCellByPosition(1, 0)
   cell.setString("")
   text       = cell.getText()
   textcursor = text.createTextCursor()
   urlfield   = sprd.createInstance("com.sun.star.text.TextField.URL")
   urlfield.setPropertyValue("Representation", ds[1])
   urlfield.setPropertyValue("URL", "#%s" % (m.detailrange))
   text.insertTextContent(textcursor, urlfield, False)
   memberindexdict[sheetname]['visited'] += 1
# ---------------------------------------------------------------------------
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
def fetchMembers() :
    """
    Get Django objects, which implicitly opens a database connection
    return the member manager, from which everything else is accessible
    Throw ImportError if Django project cannot be found
    """
    return Member.objects.all()
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
    parser.add_option("-s", "--spreadsheet", action="store",      type="string", dest="spread",   help="Partial path and name of Spreadsheet for Fido membership data", metavar="SPREAD", default="")
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
    formatSpread(sprd)

    # Get django FIDO member objects
    members = fetchMembers()

    for m in members.iterator() :
        detailMember(m, sprd)
        for key in memberindexdict.iterkeys() :
            makeDirectory(m, sprd, key)
        print("%05d (%s)..." % (m.memberid, m.last))
    sprd.store()
    dsk.terminate()
    print("Contact histogram...")
    for key in statushistogram.keys() :
        print ("%s: % 8d" % (key, statushistogram[key]))
    print("Done")
# ---------------------------------------------------------------------------
if __name__ == '__main__' :
    main()
