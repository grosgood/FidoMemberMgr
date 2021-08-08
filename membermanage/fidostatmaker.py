#! `which python`

import argparse
import genstatistics
import inspect
import os
import re

def getdispatcher() :
    """Build a dispatcher dictionary of genstatistics functions"""
    us           = 'genstatistics'
    publicre     = re.compile(r'^[^_]+')
    everything   = globals()
    allfunctions = filter(inspect.isfunction, dict(inspect.getmembers(everything[us])).values())
    pubfunctions = filter(lambda f: publicre.match(f.func_name), allfunctions)
    modfuncs     = zip(map(inspect.getmodule, pubfunctions), pubfunctions)
    modfuncs     = filter(lambda mn: us == mn[0].__name__, modfuncs)
    return dict(map(lambda mf: (mf[1].func_name, {'function':mf[1], 'doc': mf[1].func_doc}), modfuncs))

def printservices(dispatcher) :
    """Collect documentation from the given dispatcher on service
    names and associated help text bits.
    dispatcher: dictionary returned by getdispatcher"""
    return map(lambda itm: "   {0}: {1}".format(itm['function'].func_name, itm['doc']), dispatcher.itervalues())
# ---------------------------------------------------------------------------
if __name__ == '__main__' :
    dr_re     = re.compile(r'\n\n')
    r_re      = re.compile(r'\n\s*')
    mediaroot = genstatistics.__getmediaroot()
    cmdparser = argparse.ArgumentParser(description='Generates current statistical charts and thumbnails depicting aspects of the FIDO membership database. For each chart, this script makes full- and thumbnail-size Portable Network Graphics (PNG) image files.')
    cmdparser.add_argument('charts', metavar='CHARTS', nargs='+', help='List of needed charts.')
    cmdparser.add_argument('-v', '--verbose', action='store_true', default=False, help='Print informational, warning, and error messages; completely quiet otherwise (default).')
    dispatch  = getdispatcher()
    request   = cmdparser.parse_args()
    if len(request.charts) :
        checkers  = map(lambda p: (set([p]), re.compile(p, flags=re.IGNORECASE)), request.charts)
        valids    = []
        ok        = []
        unused    = set(request.charts)
        for chkr in checkers :
            for service in dispatch.iterkeys() :
                if chkr[1].search(service) :
                    cmd     = list(chkr[0])[0]
                    valids.append((cmd, dispatch[service]['function']))
                    unused.difference_update(chkr[0])
                    doclist = dr_re.split(dispatch[service]['doc'])
                    funcdoc = r_re.sub(' ', doclist[0])
                    docfp = open(os.path.join(mediaroot, "{0}_doc.txt".format(cmd)), 'wb')
                    docfp.write(funcdoc)
                    docfp.close()
                    break
        for chk in unused :
            print "Chart not found: {0}".format(list(chk)[0])
        if len(valids) :
            ok = map(lambda f: (f[0], f[1](fname=f[0])), valids)
            if len(ok) > 0 and bool(all(map(lambda f: f[1], ok)) and request.verbose) :
                print "Success."
            elif request.verbose :
                print "Some of the charts in your request failed to render."
                for pair in ok :
                    if not pair[1] :
                        print "Failed to render {0}.".format(pair[0])
        elif request.verbose :
            print "Can't find any of the charts in your request. These are the charts I know how to make:"
            for meaculpa in printservices(dispatch) :
                print meaculpa
    elif request.verbose == True :
        print "Expected a list of chart names. These are the charts I know how to make:"
        for meaculpa in printservices(dispatch) :
            print meaculpa
