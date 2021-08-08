"""
reviewmodels.py
"""

from django.db import models
import fidoonline.membermanage.models as fidomodels
# ===============================================================================
class DuesReviewManager(models.Manager) :
    """
    Create a temporary table which persists only for the connection
    """
    def checktable (self) :
        from django.db import connection
        cursor = connection.cursor()
        rc0 = cursor.execute('show tables')
        rc = False
        if rc0 :
            for ttuple in cursor :
                if ttuple[0] == u'DuesReview' :
                    rc = True
                    break
        cursor.close()
        return rc
    # ---------------------------------------------------------------------------
    def __init__ (self) :
        from django.db import connection
        import datetime
        if not self.checktable() :
            cursor = connection.cursor()
            cursor.execute('CREATE TEMPORARY TABLE DuesReview ENGINE Memory AS SELECT Member.MemberID AS \'MemberID\', Member.First as \'Firstname\', Member.Last AS \'Lastname\', findMemberTermStart(Member.MemberID) AS \'Begin\', findMembersActivePayments(Member.MemberID) AS \'Payments\', findMemberTermStart(Member.MemberID) + interval if(findMembersActivePayments(Member.MemberID), findMembersActivePayments(Member.MemberID), 1) year AS \'End\', sum(`Dues`.`PayAmount`) AS \'TotalDues\', to_days(findMemberTermStart(Member.MemberID) + interval if(findMembersActivePayments(Member.MemberID), findMembersActivePayments(Member.MemberID), 1) year) - to_days(curdate()) AS \'Expiry\' FROM (Member join Dues) WHERE Member.MemberID = Dues.MemberID GROUP BY Dues.MemberID ORDER BY Dues.MemberID')
            cursor.execute('ALTER TABLE DuesReview ADD PRIMARY KEY(MemberID)')
            cursor.execute('ALTER TABLE DuesReview ADD KEY MemberIndex (`Lastname`(10), `Firstname`(7))')
            cursor.execute('ALTER TABLE DuesReview ADD KEY ExpiryIndex (`Expiry`)')
            cursor.close()
            self.tablestart = datetime.datetime.now()
        super(DuesReviewManager, self).__init__()
# =====================================================================================    
class DuesReview (models.Model) :
    """
    CREATE TEMPORARY TABLE DuesReview
      AS SELECT
        Member.MemberID                                                                                                                                                                  AS 'MemberID',
        Member.First                                                                                                                                                                     AS 'Firstname',
        Member.Last                                                                                                                                                                      AS 'Lastname',
        findMemberTermStart(Member.MemberID)                                                                                                                                             AS 'Begin',
        findMembersActivePayments(Member.MemberID)                                                                                                                                       AS 'Payments',
        findMemberTermStart(Member.MemberID) + interval if(findMembersActivePayments(Member.MemberID), findMembersActivePayments(Member.MemberID), 1) year                               AS 'End',
        sum(`Dues`.`PayAmount`)                                                                                                                                                          AS 'TotalDues',
        to_days(findMemberTermStart(Member.MemberID) + interval if(findMembersActivePayments(Member.MemberID), findMembersActivePayments(Member.MemberID), 1) year) - to_days(curdate()) AS 'Expiry'
        FROM (Member join Dues)
        WHERE Member.MemberID = Dues.MemberID
        GROUP BY Dues.MemberID
        ORDER BY Dues.MemberID;
    """
    duesmanager  = DuesReviewManager()
    memberid     = models.OneToOneField (fidomodels.Member, primary_key = True, editable = False, verbose_name ='member id', db_column = 'MemberID' )
    firstname    = models.CharField     (max_length = 50, editable = False, null = True, db_column = 'Firstname')
    lastname     = models.CharField     (max_length = 50, editable = False, null = True, db_column = 'Lastname')
    begin        = models.DateTimeField (editable = False, null = True, db_column = 'Begin')
    payments     = models.IntegerField  (editable = False, null = True, db_column = 'Payments')
    end          = models.DateTimeField (editable = False, null = True, db_column = 'End')
    totaldues    = models.DecimalField  (max_digits = 32, decimal_places=2, editable = False, null = True, db_column = 'TotalDues')
    expiry       = models.IntegerField  (editable = False, null = True, db_column = 'Expiry')
# =====================================================================================
    class Meta :
        """
        Qualifications for the DuesReview Model
        """
        db_table  = 'DuesReview'
        managed   = False
        ordering  = ['memberid']
        
    # ---------------------------------------------------------------------------    
    def __unicode__(self) :
        return '%s %s started: %s. Days until expiration: %d' % (self.firstname, self.lastname, self.begin.ctime(), self.expiry)

