#! /usr/bin/python 
"""
localkeyring.py
A wrapper around the Gnome Key Ring for the user account
under which the middleware runs. Keys in this ring contain
database login credentials. If the script calling this module
isn't running in a context where the keyring is already open,
this script will likely throw exceptions. Defining and opening 
this keyring happens entirely outside this script in an entirely 
separate administrative operation. It is entirely opaque to us
how this might happen. Ignorance is bliss: the less we know, the
less we can give up during tort -- ah! forgive us; 'extreme
interrogation techniques.' ;)
"""
try :
    import gnomekeyring as gk
    from gnomekeyring import IOError, BadArgumentsError, NoSuchKeyringError, DeniedError 
except ImportError :
    raise ImportError ("This script requires the installation of Python bindings to the Gnome Key Ring.")
import os
creddict = None
# ---------------------------------------------------------------------------
def getcorecredentials(keyringid) :
    """
    Ask for the database credentials from (an already open) keyring
    and return a string representing the database. 
    in:  keyringid - a string identifying the (already open) keyring
    out: credentials - a dictionary object - or None if a correctly named key is not in the ring.
    raises SystemError if the key ring daemon isn't running  
    raises RuntimeError if the key ring is closed to us,the key has not been installed
           or the environment does not contain a definition for LOCALKEYNAME
    """
    global creddict
    itm = None
    if gk.is_available() :
        # Expect an open keyring given by 'keyringid'.
        # If it is not open, we won't be able to open
        # it. 
        if keyringid in gk.list_keyring_names_sync() :
            # Our key ring exists. Try to fetch our key.
            for i in gk.list_item_ids_sync(keyringid) :
                try :
                    itm = gk.item_get_info_sync(keyringid, i)
                except IOError :
                    raise RuntimeError ('The Gnome Key Ring %s is currently locked and needs to be opened by some other means, probably involving another password for the keyring itself. With the keyring locked, we cannot obtain database credentials.' % (keyringid))
                try :
                    if itm.get_display_name() == os.environ['LOCALKEYNAME'] :
                        # Ooooh. Dirty secrets...
                        creddict = gk.item_get_attributes_sync(keyringid, i)
                        creddict.update({'secret': itm.get_secret()})
                        return creddict
                except KeyError :
                    # The environment references a non-existing key or
                    # else the prequisite environmental variable has
                    # itself not been defined.
                    # Plead stupidity in a run time exception.
                    raise RuntimeError ('LOCALKEYNAME must be defined in the environment and set to the name of an already-defined key on the keyring. Lacking this, we cannot obtain database credentials. ')
        else :
            # 'keyringid' hasn't been defined.
            #  Raise a runtime error.
            raise RuntimeError ('A key ring named: %s has not been defined. Cannot obtain database login credentials.' % (keyringid))
            
    else :
        # Not even a keyring subsystem around. What is the world coming to? 
        # Raise an exception.
        raise SystemError("Key Ring subsystem is not available. Cannot obtain database connection information or credentials.") 
# ---------------------------------------------------------------------------
def getDatabaseName(keyringid) :
    """
    Furnish the name of the database the application should access

    in: name of keyring
    out: string, a database name.
    raises SystemError if the Gnome Key Ring is not available
    raises RuntimeError if the keyring or key is unavailable, or we don't have permission
    to obtain the key
    """
    global creddict

    if not creddict :
        creddict = getcorecredentials(keyringid)
        if not creddict :
            raise RuntimeError('Unable to obtain database credentials.')
    try :
        return creddict['database']
    except KeyError :
        raise RuntimeError('The key does not furnish the name of the application\'s database.') 
# ---------------------------------------------------------------------------
def getDatabaseUser(keyringid) :
    """
    Furnish the name of a database user credentialed to obtain data 

    in: name of keyring
    out: string, a database user name. Presumed to be defined in the database
    raises SystemError if the Gnome Key Ring system is not available
    raises RuntimeError if the keyring or key is unavailable, or we don't have permission
    to obtain the key
    """
    global creddict

    if not creddict :
        creddict = getcorecredentials(keyringid)
        if not creddict :
            raise RuntimeError('Unable to obtain database credentials.')
    try :
        return creddict['username']
    except KeyError :
        raise RuntimeError('The key does not furnish the name of a database user.') 
# ---------------------------------------------------------------------------
def getDatabaseSecret(keyringid) :
    """
    Furnish the name of a database password 
    in: name of keyring
    out: string, a password (the secret).
    raises SystemError if the Gnome Key Ring is not available
    raises RuntimeError if the keyring or key is unavailable, or we don't have permission
    to obtain the key
    """
    global creddict

    if not creddict :
        creddict = getcorecredentials(keyringid)
        if not creddict :
            raise RuntimeError('Unable to obtain database credentials.')
    try :
        return creddict['secret']
    except KeyError :
        raise RuntimeError('The key does not furnish a database passphrase or secret.') 
# ---------------------------------------------------------------------------
if __name__ == '__main__' :
   """
   Module testbed. This testbed will throw exceptions unless the process owner
   running this script has rights to the key ring name given on the command line, 
   the key defined by the environmental variable 'LOCALKEYNAME' is on the ring
   and the key on the Gnome key ring possesses all the needed items. If this script
   constantly throws exceptions on you and you can't get any credentials, you probably
   aren't the right login user.
   """
   import sys

   if len(sys.argv) > 1 :
       print "Database: %s" % (getDatabaseName(sys.argv[1]))
       print "User:     %s" % (getDatabaseUser(sys.argv[1]))
       print "Secret:   %s" % (getDatabaseSecret(sys.argv[1]))
   else :
       print 'usage: %s <keyring name> : Supply a keyring name. It should already possess a key named by the enviromental variable: \'LOCALKEYNAME\'' % (sys.argv[0])
