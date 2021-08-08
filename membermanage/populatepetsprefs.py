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

# ---------------------------------------------------------------------------
def checkpets(conn) :
    """
    """
    i_cursor = conn.cursor()
    o_cursor = conn.cursor()
    rc0 = o_cursor.execute('show tables')
    tlset  = set([t[0] for t in o_cursor.fetchall()])
    if tlset.issuperset(set(['PetTemp'])) :
        o_cursor.execute('DROP TEMPORARY TABLE IF EXISTS PetTemp')
    o_cursor.execute('create temporary table PetTemp as select * from Pet order by PetID')
    # Migrate via the relations with owners
    rc0 = o_cursor.execute('select distinct PetID from OwnerPetRelation order by PetID')
    if rc0 > 0 :
        for petid in o_cursor :
            rc0    = i_cursor.execute('select PetName, PetDescription from PetTemp where PetID = %s', [str(petid[0])])
            rs     = i_cursor.fetchall()[0]
            newpet = models.Pet(name=rs[0], description=rs[1])
            newpet.save()
            rc1    = i_cursor.execute('select MemberID from OwnerPetRelation where PetID = %s', [str(petid[0])])
            if rc1 :
                for m_id in i_cursor :
                    mbr     = models.Member.objects.get(pk=m_id[0])
                    newpair = models.MemberPet(member=mbr, pet=newpet)
                    newpair.save()
            i_cursor.execute('delete from PetTemp where PetID=%s', [str(petid[0])])
    rc0 = o_cursor.execute('select PetID, PetName from PetTemp order by PetName')
    if rc0 > 0 :
        if rc0 == 1 :
            print ('Unafiliated pet:')
        else :
            print ('%d unafiliated pets:' % rc0)
        for uafp in o_cursor :
            print('%d: %s',% (uafp[0], uafp[1]))
    o_cursor.execute('drop temporary table PetTemp')
    o_cursor.close()
    i_cursor.close()
# ---------------------------------------------------------------------------
def checkprefs(conn) :
    """
    """
    cursor = conn.cursor()
    rc0 = cursor.execute('select MemberID, NewsFlag, BroadcastFlag from MemberPreference order by MemberID')
    if rc0 :
        for m_id in cursor :
            ss = ''
            if m_id[1] and not m_id[2]:
                ss  = 'MailNewsletter'
            if m_id[2] and not m_id[1]:
                ss  = 'BroadcastEmail'
            if m_id[1] and m_id[2] :
                ss  = 'MailNewsletter,BroadcastEmail'
                
            membr   = models.Member.objects.get(pk=m_id[0])
            newpref = models.MemberPreference(memberid = membr, prefs = ss)
            newpref.save()
    cursor.close()
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

    # Pets
    checkpets(conn)

    # Prefs
    checkprefs(conn)

    # Cleanup
    conn.close()
# ---------------------------------------------------------------------------
if __name__ == '__main__' :
    main()
