from django.db import models

# import pydb
# ================================================================================
class MailAddress (models.Model) :
    """
    Represents a place with an associated U. S. Mail address that this object. One
    or more Members may reside at this place.
    Custom modifications: sql/mailaddress.sql
    """

    adrid    = models.AutoField(
                                 db_column    = 'AddressID',
                                 editable     = False,
                                 primary_key  = True,
                                 verbose_name = 'address identifier'
                               )

    aptnum   = models.CharField(
                                 max_length   = 20,
                                 blank        = True,
                                 db_column    = 'Apt',
                                 default      = '',
                                 help_text    = 'Apartment, room, or suite number',
                                 verbose_name = 'apartment number'
                               )
    
    city     = models.CharField(
                                 max_length   = 30,
                                 db_column    = 'City',
                                 default      = '',
                                 help_text    = 'City, which defaults to \'Brooklyn\'.',
                               )
    
    company  = models.CharField(
                                 max_length   = 50,
                                 blank        = True,
                                 db_column    = 'Company',
                                 default      = '',
                                 help_text    = 'Place of business',
                                 verbose_name = 'Business name'
                               )
    
    country  = models.CharField(
                                 max_length   = 5,
                                 db_column    = 'Country',
                                 default      = 'US',
                                 help_text    = 'Country. Defaults to \'US\'.'
                               )

    state    = models.CharField(
                                 max_length   = 5,
                                 db_column    = 'State',
                                 default      = '',
                                 help_text    = 'State, province. Defaults to \'NY\''
                               )
    
    street   = models.CharField(
                                 max_length = 50,
                                 db_column    = 'Street',
                                 default      = '',
                                 help_text    = 'House number and street'
                               )
    
    zipcode  = models.CharField(
                                 max_length = 10,
                                 db_column    = 'Postcode',
                                 help_text    = 'Primary code (US: Five digit ZIP Code)',
                                 verbose_name = 'ZIP Code'
                               )
    
    zipext   = models.CharField(
                                 max_length = 5,
                                 db_column    = 'PostcodeExt',
                                 help_text    = 'Secondary code (US: Four digit ZIP+4 Code). <a href="http://zip4.usps.com/zip4/welcome.jsp" target="uspspopup">Lookup...</a>',
                                 verbose_name = 'ZIP+4'
                               )
    class Meta :
        """
        Qualifications for the MailAddress model
        """
        db_table  = 'MailAddress'
        managed   = 'True'
        ordering  = ['zipcode', 'zipext']
        
    # ---------------------------------------------------------------------------
    def __unicode__(self) :
        """
        Make a unicode string representation of this object
        """
        cp = ""
        if len(self.company) > 0 :
            cp = "%s, " % self.company
        return "%s%s %s, %s, %s %s-%s %s" % (cp, self.street, self.aptnum, self.city, self.state, self.zipcode, self.zipext, self.country)

# ================================================================================
class TelNumber (models.Model) :
    """
    Represents a telephone number with extension
    Custom modifications: sql/telnumber.sql
    """

    telid  = models.AutoField(
                               db_column    = 'TelID',
                               editable     = False,
                               primary_key  = True,
                               verbose_name = 'telephone identifier'
                             )

    area   = models.DecimalField(
                               max_digits     = 3,
                               decimal_places = 0, 
                               db_column    = 'AreaCode',
                               help_text    = 'Three digit area code',
                               verbose_name = 'area code'
                             )
    
    exch   = models.DecimalField(
                               max_digits     = 3,
                               decimal_places = 0, 
                               db_column    = 'ExchCode',
                               help_text    = 'Three digit exchange code',
                               verbose_name = 'exchange code'
                             )
    
    number = models.DecimalField(
                               max_digits     = 4,
                               decimal_places = 0, 
                               db_column    = 'Number',
                               help_text    = 'four digit line number',
                               verbose_name = 'line number'
                             )
    
    ext    = models.DecimalField(
                               max_digits     = 4,
                               decimal_places = 0,
                               blank          = True,
                               null           = True,
                               db_column      = 'Extension',
                               help_text      = 'Four digit extension',
                               verbose_name   = 'extension'
                             )
    class Meta :
        """
        Qualifications for the TelNumber model
        """
        db_table  = 'TelNumber'
        managed   = 'True'
        ordering  = ['area', 'exch', 'number', 'ext']
    # ---------------------------------------------------------------------------
    def isempty(self) :
        """
        True if this telephone number consists of all empty fields
        """
        return self.area == None and self.exch == None and self.number == None and self.ext == None
    # ---------------------------------------------------------------------------
    def __unicode__ (self) :
        """
        Represent a telephone number as a string
        """
        extension = ""
        if self.isempty() :
            return "No telephone."
        elif self.ext and self.ext != 0 :
            extension = " Ext: %04d" % (self.ext)
        return "%03d-%03d-%04d %s" % (self.area, self.exch, self.number, extension)
    
# ================================================================================
class EMailAddress (models.Model) :
    """
    Represents an electronic mail address in a two part name '@' host form, with
    the commercial 'at' symbol implicitly sitting between the two fields.
    Custom modifications: sql/emailaddress.sql
    """

    adrid  = models.AutoField(
                               db_column    = 'EMailID',
                               editable     = False,
                               primary_key  = True,
                               verbose_name = 'email identifier'
                             )

    name   = models.CharField(
                               max_length   = 30,
                               db_column    = 'EMailName',
                               help_text    = 'Mailbox name',
                               verbose_name = 'box name'
                             )
    
    domain = models.CharField(
                               max_length   = 30,
                               db_column    = 'EMailDomain',
                               help_text    = 'Mailbox domain',
                               verbose_name = 'server name'
                             )
    class Meta :
        """
        Qualifications for the EMailAddress model
        """
        db_table  = 'EMailAddress'
        managed   = 'True'
        ordering  = ['domain', 'name']
        
    # ---------------------------------------------------------------------------
    def __unicode__ (self) :
        """
        Represent an email object as a string
        """
        return "%s@%s" % (self.name, self.domain)
    
# ================================================================================
class Member (models.Model) :
    """
    Documents the member's name and associated unique member ID.
    Custom modifications: sql/member.sql
    """
    sal_types = (
                   ('Dr.',  'Dr.'),
                   ('Hon.', 'Hon.'),
                   ('Miss', 'Miss'),
                   ('Mr.',  'Mr.'),
                   ('Mrs.', 'Mrs.'),
                   ('Ms.',  'Ms'),
                   ('Sir',  'Sir'),
                   ('',     'None'),
                )
    
    memberid  = models.PositiveSmallIntegerField(
                                                  db_column    = 'MemberID',
                                                  editable     = False,
                                                  primary_key  = True,
                                                  unique       = True,
                                                  verbose_name = 'member identifier'
                                                )

    mailadr   = models.ForeignKey(
                                   MailAddress,
                                   blank        = True,
                                   related_name = 'homeaddress',
                                   db_column    = 'AddressID',
                                   help_text    = 'Pull down an existing address or add (green cross).',
                                   null         = True,
                                   verbose_name = 'mail address'
                                 )

    emailadr   = models.ForeignKey(
                                   EMailAddress,
                                   blank        = True,
                                   related_name = 'emailaddress',
                                   db_column    = 'EMailID',
                                   help_text    = 'Pull down an existing email address or add (green cross)',
                                   null         = True,
                                   verbose_name = 'email address'
                                 )

    telnumber  = models.ForeignKey(
                                   TelNumber,
                                   blank        = True,
                                   related_name = 'telphone',
                                   db_column    = 'TelID',
                                   help_text    = 'Pull down an existing telephone number or add (green cross).',
                                   null         = True,
                                   verbose_name = 'telephone number'
                                 )
    
    salute    = models.CharField (
                                   max_length   = 5,
                                   blank        = True,
                                   choices      = sal_types,
                                   db_column    = 'Salute',
                                   default      = '',
                                   help_text    = 'Member\'s title.',
                                   verbose_name = 'salutation', 
                                 )

    first     = models.CharField (
                                   max_length   = 50,
                                   db_column    = 'First',
                                   help_text    = 'Member\'s \'first\'  name',
                                   verbose_name = 'first name'
                                 )

    middle    = models.CharField (
                                   max_length   = 50,
                                   blank        = True,
                                   db_column    = 'Middle',
                                   default      = '',
                                   help_text    = 'Member\'s \'middle\' name or initial',
                                   verbose_name = 'middle name'
                                 )

    last     = models.CharField  (
                                   max_length   = 50,
                                   db_column    = 'Last',
                                   help_text    = 'Member\'s \'last\' name',
                                   verbose_name = 'last name'
                                 )

    suffix   = models.CharField (
                                   max_length   = 5,
                                   blank        = True,
                                   db_column    = 'Suffix',
                                   default      = '',
                                   help_text    = 'A suffix such as \'III\' or \'Jr\''
                                 )
    class Meta :
        """
        Qualifications for the Member model
        """
        db_table  = 'Member'
        managed   = 'True'
        ordering  = ['last', 'first']

    def __unicode__ (self) :
        """
        Make a unicode string representation of this object
        """
        nm = ""
        if self.memberid > 0 :
            nm += "%05d " % self.memberid
        if len(self.salute) > 0 :
            nm += "%s " % self.salute 
        if len(self.first)  > 0 :
            nm += "%s " % self.first 
        if len(self.middle) > 0 :
            nm += "%s " % self.middle
        if len(self.last)   > 0 :
            nm += "%s" % self.last
        if len(self.suffix) > 0 :
            nm += " %s" % self.suffix
        return nm
    # ---------------------------------------------------------------------------
    def calcTerm (self) :
        """
        Given dues payments, find beginning and end of current term, comprised of
        a series of payments not greater than a year apart.
        """
        import datetime as dt
        now          = dt.datetime.now() 
        dpay         = Dues.objects.filter(memberid__exact=self.memberid)
        paycount     = dpay.count()
        if paycount > 0 :
            term_start   = dpay[0].paydate
            term_length  = 1
            for i in range(1, paycount) :
                term_end = dt.datetime(term_start.year + term_length, term_start.month, term_start.day, term_start.hour, term_start.minute, term_start.second)
                if (dpay[i].paydate - term_end).days >= 0 : # Expiration event: reset term start to date payment was made, term length to 1
                    term_start    = dpay[i].paydate
                    term_length  = 1
                else : # At ith payment, member still active, or expiring, when payment was made so extend the term. 
                    term_length += 1
            term_end    = dt.datetime(term_start.year + term_length, term_start.month, term_start.day, term_start.hour, term_start.minute, term_start.second)
            expiry      = (term_end - now).days
        else :
            # raise RuntimeError, "Member {0} has no payment records.".format(self.memberid)
            term_start = now
            term_end   = now
            expiry     = 0
        return {'start' :term_start, 'end': term_end,  'expiry': expiry}

    term   = property(calcTerm, doc='Member\'s most recent term of activity: 3-tuple of term start and end and days until expiry.')
    expiry = property(lambda s: s.calcTerm()['expiry'], doc='Member\'s current term\'s expiry date.')
    start  = property(lambda s: s.calcTerm()['start'], doc='Member\'s start of his or her\'s current term.')
    end    = property(lambda s: s.calcTerm()['end'], doc='Member\'s last day in his or her\'s current term.')
    # ---------------------------------------------------------------------------
    def getContactStatusFlags (self) :
        """
        returns 0 - Lost All Contact, 1 - Telephone Only, 2 - EMail Only,   3 - No US Mail
                4 - US Mail Only,     5 - No Email        6 - No Telephone, 7 - OK 
        """
        return bool(self.mailadr)*4 + bool(self.emailadr)*2 + bool(self.telnumber)
    contactstatusText = ['Lost All Contact', 'Telephone Only', 'EMail Only',   'No US Mail', 'US Mail Only', 'No Email', 'No Telephone', 'OK'] 
    contactStatus     = property(lambda s: s.contactstatusText[s.getContactStatusFlags()], doc='Furnishes available means to contact a FIDO member.')
    # ---------------------------------------------------------------------------
    def nextMemberID (self) :
        """
        Provide a new member number. Let this be the highest
        extant member identifier in the table and increment this by one. Should the
        table be empty, begin at member number 1
        """
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute('SELECT IFNULL(MAX(`Member`.`MemberID`), 0) from `Member`')
        nxt = cursor.fetchall()[0][0] + 1
        cursor.close()
        return nxt
    # ---------------------------------------------------------------------------
    def save(self, force_insert=False, force_update=False) :
        """
        Extend parent save. Check for the existence of an initialized memberID.
        If it is not initialized, fetch a new identifier number. Request locks
        to prevent a race with other sessions that may be establishing new members
        as well.
        """
        from django.db import connection

        cursor = connection.cursor()
        cursor.execute('LOCK TABLES `Member` WRITE')
        if not self.memberid :
            # New object. Assign the next ID. 
            self.memberid = self.nextMemberID()
         # Call parent's save() method
        super(Member, self).save(force_insert, force_update)
        cursor.execute('UNLOCK TABLES')
        cursor.close()
        
# ================================================================================
class MemberPet (models.Model) :
    """
    Pairing of a particular member with a particular pet. The member may pair with
    other pets and the pet may have other pairings with members, these represented
    by other pairing records.
    Custom modifications: sql/memberpet.sql
    """
    mpid   = models.AutoField(
                               db_column    = 'MemberPetID',
                               editable     = False,
                               primary_key  = True,
                               verbose_name = 'pairing identifier'
                             )

    member = models.ForeignKey(
                                'Member',
                                db_column    = 'MemberID',
                                verbose_name = 'member identifier'
                              )

    pet    = models.ForeignKey(
                                'Pet',
                                db_column    = 'PetID',
                                verbose_name = 'pet identifier'
                              )

    class Meta :
        """
        Qualifications for the MemberPet model
        """
        db_table  = 'MemberPet'
        managed   = 'True'
        ordering  = ['member', 'pet']

    # ----------------------------------------------------------------------------
    def __unicode__(self) :
        """
        Return a string representing the member-pet pair in this relationship
        """
        return "%s - %s" % (str(Member.objects.get(pk=member)), str(Pet.objects.get(pk=pet)))
# ================================================================================
class Pet (models.Model) :
    """
    Name and description of a pet owned or co-owned by a number of members. The
    many-to-many association with members is through the MemberPet mapping table.
    A pet may also have a 'Dog Tag' issued by FIDO and bearing a simple Tag ID
    number which serves to identify a FIDO member's dog. See the DogTag table. 
    Custom modifications: sql/pet.sql
    """
    petid      = models.AutoField(
                                  db_column    = 'PetID',
                                  editable     = False,
                                  primary_key  = True,
                                  verbose_name = 'pet identifier'
                                )

    memberrel     = models.ManyToManyField(
                                           Member,
                                           through   =  MemberPet
                                          )
    name          = models.CharField (
                                      max_length   = 50,
                                      db_column    = 'Name',
                                      help_text    = 'Pet\'s  name',
                                      verbose_name = 'pet name'
                                     )
    description   = models.TextField(
                                     db_column = 'Description',
                                     blank     = True,
                                     null      = True,
                                     help_text = 'Freeform details describing the pet; consider usefulness for a lost pet poster.'
                                    )
    # ----------------------------------------------------------------------------
    def __unicode__(self) :
        """
        String representation of the Pet model.
        """
        return '%s %s' % (str(self.petid), self.name)

    class Meta :
        """
        Qualifications for the Pet model
        """
        db_table  = 'Pet'
        managed   = 'True'
        ordering  = ['name', 'petid']

# ================================================================================
class DogTag (models.Model) :
    """
    On 05-Jun-2010 FIDO commenced issuing tags to members' dogs. The
    tags help to identify and retrieve a dog which may become
    misplaced. Finders may report the dog tag ID to FIDO; FIDO looks
    up the tag to find the association with the dog A dog may have a
    one-to-many relationship with tags, as lost tags are still
    associated with the last known dog that had such. The dog has a
    many-to-many relationship with FIDO members, expressed through the
    MemberPet table. This association may turn up one, two,
    three... individuals associated with the dog in question, but in
    any case, FIDO has a contact list to alert people owning the dog
    that their pet has been found.

    27-July-2010 - Dogs may have multiple FIDO tags, arising from the
    'Lost Tag' case; we keep the lost tag associated with the dog, but
    mark the new field, 'TagStatus' as 'Lost' instead of
    'Assigned'. Assertion needing an edit check: A dog may only have
    one Tag with an 'Assigned' TagStatus (all other dog tags
    associated with the dog must be 'Lost').

    Custom modifications: sql/dogtag.sql
    """
    import datetime
    statclasses   = (
                      ('Available', 'FIDO has not given out this tag'), 
                      ('Assigned',  'The tag has been given to a FIDO Member'),
                      ('Lost',      'The tag has been reported lost')
                    )
  
    petid = models.ForeignKey  (
                                      Pet,
                                      db_column    = 'PetID',
                                      editable     = False,
                                      verbose_name = 'tagged pet'
                                )
    
    tagnumber = models.IntegerField (
                                      blank        = False,
                                      db_column    = 'Tag',
                                      editable     = True,
                                      primary_key  = True,
                                      null         = False,
                                      default      = 0,
                                      verbose_name = 'tag number'
                                    )
    
    issuedate = models.DateField (
                                      blank        = False,
                                      db_column    = 'IssueDate',
                                      default      = datetime.datetime.now, 
                                      editable     = True,
                                      null         = False,
                                      verbose_name = 'issue date'
                                 )
    tagstatus = models.CharField(
                                      max_length   = 15,
                                      db_column    = 'TagStatus',
                                      editable     = False,
                                      choices      = statclasses,
                                      verbose_name = 'tag status'
                                )
    def __unicode__(self) :
        """
        String representation of the DogTag model.
        """
        return '%s %s' % (str(self.tagnumber), self.tagstatus)

    class Meta :
        """
        Qualifications for the DogTag Model
        """
        db_table  = 'DogTag'
        managed   = 'True'
        ordering  = ['petid']

# ================================================================================
class MemberPreference (models.Model) :
    """
    FIDO services which members may elect to have; inclusion in the preference
    set indicates the member wishes to subscribe; its absence indicates otherwise. 
    Custom modifications: sql/memberpreference.sql
    """
    prefclasses   = (
                      ('MailNewsletter',  'Send the newsletter through U. S. Mail'), 
                      ('BroadcastEmail',  'Send broadcast email')
                    )
    
    memberid = models.OneToOneField(
                                     Member,
                                     db_column    = 'MemberID',
                                     editable     = False,
                                     primary_key  = True,
                                     verbose_name = 'member preference'
                                   )
    
    prefs    = models.CharField(
                                 max_length  = 30,
                                 choices     = prefclasses,
                                 db_column   = 'Preferences',
                                 help_text   = 'Include services that the member would like to have.'
                               )
    class Meta :
        """
        Qualifications for the MemberPreference Model
        """
        db_table  = 'MemberPreference'
        managed   = 'True'
        ordering  = ['memberid']
        
# --------------------------------------------------------------------------------
    def __unicode__(self) :
        pstr = ", ".join(self.prefs.split(','))
        if len(pstr) :
            return "Preferencs: %s" % pstr
        else :
            return "No preferences."
        
# ================================================================================
class Journal (models.Model) :
    """
    A text entry associated with a member; the title indicates the nature of the
    entry. 
    Custom modifications: sql/journal.sql
    """
    entryclasses  = (
                      ('Address',        'postal address changes'),
                      ('Correspondence', 'member correspondence (to/from).'),
                      ('Deletion',       'note removal to archive'),
                      ('Payment',        'payments (form/details)'),
                      ('EMail',          'email changes'),
                      ('Identity',       'member name changes.'),
                      ('Initial',        'application details'),
                      ('Mailing',        'mailings: date sent, address'),
                      ('Pet',            'pet name/description.'),
                      ('Preference',     'member preferences'),
                      ('Remark',         'non-specific matters'),
                      ('Telephone',      'telephone changes.')
                    )

    journalid = models.AutoField(
                                  db_column    = 'JournalID',
                                  primary_key  = True,
                                  editable     = False,
                                  verbose_name = 'journal entry'
                                )

    memberid  = models.ForeignKey(
                                   Member,
                                   db_column    = 'MemberID',
                                   help_text    = 'Subject of this Journal entry.',
                                   verbose_name = 'member identifier'
                                 )
    
    entrydate = models.DateTimeField(
                                      auto_now      = False,
                                      auto_now_add  = True,
                                      db_column     = 'EntryDate',
                                      help_text     = 'The date and time of the journal entry',
                                      verbose_name  = 'entry date'
                                    )

    entrytype = models.CharField(
                                  max_length   = 15,
                                  choices      = entryclasses,
                                  db_column    = 'Subject',
                                  help_text    = 'Topic which the Journal entry is about',
                                  verbose_name = 'entry type'
                                )
    
    comment   = models.TextField(
                                  db_column = 'Comment',
                                  help_text = 'Freeform details expanding on the subject of the journal entry.'
                                )

    class Meta :
        """
        Qualifications for the Journal Model
        """
        db_table  = 'Journal'
        managed   = 'True'
        ordering  = ['entrydate', 'memberid', 'entrytype']
        
    # ---------------------------------------------------------------------------
    def __unicode__ (self) :
        """
        Make a string representation of a Journal entry
        """
        return "%s %s: %s." % (str(self.entrytype), str(self.memberid), self.entrydate.ctime())

# ================================================================================
class Dues (models.Model) :
    """
    Represents a single payment of dues to FIDO on a particular date. 
    Custom modifications: sql/dues.sql
    """

    paytypes  = (
                   ('New',       'new'),
                   ('Renew',     'renewing'),
                   ('Reinstate', 'reinstatement.')
                )
    
    duesid    = models.AutoField(
                                  db_column    = 'DuesID',
                                  editable     = False,
                                  primary_key  = True,
                                  verbose_name = 'payment identifier'
                                )

    memberid  = models.ForeignKey(
                                    Member,
                                    db_column    = 'MemberID',
                                    verbose_name = 'Member identifier'
                                  )
    
    journalid = models.ForeignKey(
                                    'Journal',
                                    blank        = True,
                                    null         = True,   
                                    db_column    = 'JournalID',
                                    verbose_name = 'Payment details'
                                  )

    paydate   = models.DateTimeField(
                                      auto_now      = False,
                                      auto_now_add  = True,
                                      db_column     = 'PayDate',
                                      verbose_name  = 'Payment Date'
                                    )

    payamount = models.DecimalField(
                                      max_digits     = 10,
                                      decimal_places =  2, 
                                      db_column      = 'PayAmount',
                                      help_text      = 'Amount of payment in US dollars.',
                                      verbose_name   = 'Payment Amount'
                                   )

    paytype   = models.CharField(
                                  max_length   = 10,
                                  choices      = paytypes,
                                  db_column    = 'PayType',
                                  help_text    = 'Payment type is one of a new member, a renewing member, or a member reinstating an expired membership.' 
                                )
    class Meta :
        """
        Qualifications for the Dues Model
        """
        db_table  = 'Dues'
        managed   = 'True'
        ordering  = ['paydate', 'paytype']
        
    # ---------------------------------------------------------------------------
    def __unicode__ (self) :
        """
        Make a string representation of a dues payment  with Amount, date,
        and payer information.
        """
        return "$%5.2f from %s on %s. %s." % (self.payamount, str(self.memberid), self.paydate.ctime(), str(self.paytype))

# ================================================================================
class MemberCard (models.Model) :
    """
    Represents membership ID cards which FIDO has issued 
    Custom modifications: sql/membercard.sql
    """
    cardid    = models.AutoField(
                                  db_column    = 'CardID',
                                  editable     = False,
                                  primary_key  = True,
                                  verbose_name = 'card identifier'
                                )

    memberid  = models.ForeignKey(
                                    Member,
                                    db_column    = 'MemberID',
                                    verbose_name = 'member identifier'
                                  )
    issuedate = models.DateTimeField(
                                      auto_now      = False,
                                      auto_now_add  = False,
                                      db_column     = 'IssueDate',
                                      verbose_name  = 'card issue date'
                                    )
    series   = models.CharField(
                                  max_length   = 15,
                                  db_column    = 'Series',
                                  help_text    = 'Name of the card\'s seasonal design, (i.e. \'Fall 2009\')',
                                  verbose_name = 'name of card\'s series'
                                )
    class Meta :
        """
        Qualifications for the MemberCard Model
        """
        db_table  = 'MemberCard'
        managed   = 'True'
        ordering  = ['memberid', 'issuedate']

    # ---------------------------------------------------------------------------
    def __unicode__ (self) :
        """
        Make a string representation of a member card
        and payer information.
        """
        return "Card %d for %s issued on %s" % (self.cardid, "%s %s" % (self.memberid.first, self.memberid.last), self.issuedate.strftime("%B %d, %Y"))
