#! /usr/bin/python
"""
Utility to populate fidomembers_ol from fidomembers via the django api
"""
import sys
import MySQLdb as mysql
import datetime
import re
from optparse import OptionParser
try :
    import Fido_Online.membermanage.models as models
except ImportError :
    sys.path.append('/media/FireTwo/FidoMembership')
    import fidoonline.membermanage.models as models
#checkjournal.pik uses this to map string patterns to Journal classes.
re_map = (
            ('Address',        re.compile(r'^address ch',    re.IGNORECASE)),
            ('Address',        re.compile(r'^address co',    re.IGNORECASE)),
            ('Address',        re.compile(r'^member',        re.IGNORECASE)),
            ('Address',        re.compile(r'^usps',          re.IGNORECASE)),
            ('Address',        re.compile(r'^zip',           re.IGNORECASE)),
            ('Correspondence', re.compile(r'^corres',        re.IGNORECASE)),
            ('Correspondence', re.compile(r'^person',        re.IGNORECASE)),
            ('Dues',           re.compile(r'^dues',          re.IGNORECASE)),
            ('Dues',           re.compile(r'^just',          re.IGNORECASE)),
            ('Dues',           re.compile(r'^web l',         re.IGNORECASE)),
            ('EMail',          re.compile(r'^bad email',     re.IGNORECASE)),
            ('EMail',          re.compile(r'^change email',  re.IGNORECASE)),
            ('EMail',          re.compile(r'^changed email', re.IGNORECASE)),
            ('EMail',          re.compile(r'^email',         re.IGNORECASE)),
            ('EMail',          re.compile(r'^new em',        re.IGNORECASE)),
            ('Identity',       re.compile(r'^name',          re.IGNORECASE)),
            ('Initial',        re.compile(r'^direct init',   re.IGNORECASE)),
            ('Initial',        re.compile(r'^import',        re.IGNORECASE)),
            ('Mailing',        re.compile(r'^senior',        re.IGNORECASE)),
            ('Mailing',        re.compile(r'^spring',        re.IGNORECASE)),
            ('Mailing',        re.compile(r'^summer',        re.IGNORECASE)),
            ('Mailing',        re.compile(r'^fall m',        re.IGNORECASE)),
            ('Pet',            re.compile(r'^added pet',     re.IGNORECASE)),
            ('Pet',            re.compile(r'^dog',           re.IGNORECASE)),
            ('Pet',            re.compile(r'^pet',           re.IGNORECASE)),
            ('Preference',     re.compile(r'^pref',          re.IGNORECASE)),
            ('Telephone',      re.compile(r'^telep',         re.IGNORECASE))
         )

# ---------------------------------------------------------------------------
def checkmember(mdata) :
    """
    Get the member corresponding to mdata['MemberID']. Create a new member
    object if it does not exist.
    """
    if mdata == None or not mdata.has_key('MemberID') :
        raise OperationalError('Expected dictionary with key \'MemberID\'')
        
    try :
        m = models.Member.objects.get(pk=mdata['MemberID'])
    except models.Member.objects.model.DoesNotExist :
        m = models.Member()
        if mdata['MemberID'] :
            m.memberid = mdata['MemberID']
        else :
            raise OperationalError("MemberID is not defined (but it should be)")
        if mdata['Salute'] :
            m.salute = mdata['Salute']
        else :
            m.salute = ''
        if mdata['First'] : 
            m.first = mdata['First']
        else :
            m.first = ''
        if mdata['Middle'] :
            m.middle = mdata['Middle']
        else :
            m.middle = ''
        if mdata['Last'] :
            m.last = mdata['Last']
        else :    
            m.last = ''
        m.suffix = ''
        m.save()
    return m
# ---------------------------------------------------------------------------
def checkcontact(m, conn) :
    """
    Get or create US mail, telephone and/or email address records for the member, m
    
    """
    import decimal
    
    mailset  = frozenset(['Good', 'No Email', 'No Telephone', 'Only US Mail', 'Suspect Mail Address'])
    emailset = frozenset(['Good', 'No Telephone', 'No Mail Address', 'Only EMail'])
    teleset  = frozenset(['Good', 'No Email', 'No Mail Address', 'Only Telephone'])
    cursor = conn.cursor()
    rc0 = cursor.execute('select `MemberContact`.`Contact Status` from MemberContact where `MemberContact`.`MemberId` = %s', [m.memberid] )
    if not rc0 :
        raise mysql.OperationalError('Member %d has no corresponding MemberContact record' % m.memberid)
    ms = set(cursor.fetchall()[0])
    schema = []
    rc0 = cursor.execute('DESCRIBE `Contact`')
    if not rc0 :
        raise mysql.OperationalError('fidomembers has no Contact table.')
    else :
        [schema.append(rw[0]) for rw in cursor]
    rc0 = cursor.execute('select * from Contact where Contact.MemberID = %s', [m.memberid])
    if not rc0 :
        raise mysql.OperationalError('Member %d has no corresponding Contact record' % m.memberid)
    
    cdict = dict(zip(schema, cursor.fetchall()[0]))
    for (k, v) in cdict.iteritems() :
        if v == None :
            cdict[k] = ''
        if k == 'Country' and v == 'U. S. A.' :
            cdict[k] = 'US'
        if k == 'HTArea' or k == 'HTPrfx' or k == 'HTNumber' or k == 'HTExtension' :
            if v == '' or v == None :
                cdict[k] = decimal.Decimal('0')
            else :
                cdict[k] = decimal.Decimal(cdict[k])
    if ms.issubset(mailset) :
        # Have a complete mail address...
        (rs, cflg) = models.MailAddress.objects.get_or_create(
                                                               street   = cdict['Street'], 
                                                               defaults = {
                                                                            'aptnum'  : cdict['Location'],
                                                                            'city'    : cdict['City'],
                                                                            'company' : cdict['Company'],
                                                                            'country' : cdict['Country'],
                                                                            'state'   : cdict['State'],
                                                                            'zipcode' : cdict['Postcode'],
                                                                            'zipext'  : cdict['PostcodeExt']
                                                                   }
                                                      )
        m.mailadr = rs
        m.save()

    if ms.issubset(emailset) :
        # Have a complete e-mail address...
        (rs, cflg) = models.EMailAddress.objects.get_or_create(
                                                                name   = cdict['EMailName'],
                                                                domain = cdict['EMailDomain']
                                                              )
        m.emailadr = rs
        m.save()
            

    if ms.issubset(teleset) :
        # Have a complete telephone
        (rs, cflg) = models.TelNumber.objects.get_or_create(
                                                             area   = cdict['HTArea'],
                                                             exch   = cdict['HTPrfx'],
                                                             number = cdict['HTNumber'],
                                                             ext    = cdict['HTExtension'],
                                                           )
        m.telnumber = rs
        m.save()
    
    cursor.close()
# ---------------------------------------------------------------------------
def checkdues(m, conn) :
    """
    Migrate the various dues payment records associated with member m.
    m - member
    conn - db connection to legacy membership database
    """
    def pik(s) :
        """
        return a selector. s is a string.
        """
        import re
        newre = re.compile(r'^new', re.IGNORECASE)
        renre = re.compile(r'^ren', re.IGNORECASE)
        reire = re.compile(r'^rei', re.IGNORECASE)
        if   newre.match(s) : return 0
        elif renre.match(s) : return 1
        elif reire.match(s) : return 2
        return None

    cursor = conn.cursor()
    rc0 = cursor.execute('select DuesID, MemberID, PayDate, PayAmount, PayType from Dues where MemberID=%s', [m.memberid] )
    if rc0 == 0 :
        raise mysql.OperationalError('No Dues records found for %05d: %s %s' % (m.memberid, m.first, m.last))
    schema = [s[0] for s in cursor.description]
    for dp in cursor :
        pdict  = dict(zip(schema, dp))
        njr = models.Journal(
                               memberid  = m,
                               entrytype = 'Remark',
                               comment   = 'Migrated Dues payment %s for %4.2f. Original date: %s' % (pdict['DuesID'], pdict['PayAmount'], pdict['PayDate'].isoformat())
                            )
        njr.save()
        ndp = models.Dues(
                           duesid    = pdict['DuesID'],
                           memberid  = m,
                           journalid = njr,
                           payamount = "%4.2f" % (pdict['PayAmount']), 
                           paytype   = 'New' 
                         )
        ndp.save()
        ndp.paytype = ndp.paytypes[pik(pdict['PayType'])][0]
        ndp.paydate = pdict['PayDate']
        ndp.save()
    cursor.close()
# ---------------------------------------------------------------------------
def checkjournal(m, conn) :
    """
    Transcribe old journal entries - cleanse of internal newlines and choose
    journal entry classes heuristically from start string patterns of the current
    log titles. Renumber dataset, dropping old identifiers and poster identifier
    """
    import re
    
    def pik(s) :
        """
        Employ initial string patterns of journal log titles to select an appropriate
        journal entry class. Return the class identifying string.
        """
        global re_map
        
        for t in re_map :
            if t[1].match(s) : return t[0]
        return 'Remark'

    cursor = conn.cursor()
    rc0 = cursor.execute('select JournalID, MemberID, Timestamp, LogTitle, LogComment from Journal where MemberID=%s order by Timestamp', [m.memberid])
    if rc0 == 0 :
        raise mysql.OperationalError('No Journal records found for %05d: %s %s' % (m.memberid, m.first, m.last))
    schema = [s[0] for s in cursor.description]
    for jp in cursor :
        jdict  = dict(zip(schema, jp))
        # convert newline characters in comments to spaces - leave formatting to the renderers
        jdict['LogComment'] = " ".join(jdict['LogComment'].split("\n"))
        njr = models.Journal(
                               memberid  = m,
                               entrytype = pik(jdict['LogTitle']),
                               comment   = "Subject: %s - %s" % (jdict['LogTitle'], jdict['LogComment'])   
                            )
        njr.save()
        # Retroactively date entry to that from the source database record.
        njr.entrydate = jdict['Timestamp']
        njr.save()
    cursor.close()
# ---------------------------------------------------------------------------
def checkpets(m, conn) :
    """
    """
    pass
# ---------------------------------------------------------------------------
def checkprefs(m, conn) :
    """
    """
    pass
# ---------------------------------------------------------------------------
def main() :
    """
    """
    import  Fido_Online.membermanage.models as models

    # Get database
    try :
        conn = mysql.connect(db='fidomembers', passwd='Fido47Friends', user='gosgood', host='localhost')
    except mysql.OperationalError :
        print("Could not access the FIDO Members database. Is your username or password correct? Has the database been installed?")
        raise mysql.OperationalError    
    cursor = conn.cursor()

    # Members
    schema = []
    rc0 = cursor.execute('DESCRIBE `Member`')
    if rc0 :
        [schema.append(rw[0]) for rw in cursor]
    else :
        raise mysql.OperationalError('Could not find Member in fidomembers database.')

    # For every FIDO Member...
    rc0 = cursor.execute('select MemberID, Salute, First, Middle, Last from Member order by MemberID')
    if rc0 :
        for mrec in cursor :
            curdict = dict(zip(schema, mrec))
            m = checkmember(curdict)
            checkcontact(m, conn)
            checkdues(m, conn)
            checkjournal(m, conn)
            checkpets(m, conn)
            checkprefs(m, conn)
            print ("Migrated %s." % str(m))
    else :
        raise mysql.OperationalError('Member table is not populated.')
# ---------------------------------------------------------------------------
if __name__ == '__main__' :
    main()
