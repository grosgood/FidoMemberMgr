#!/usr/bin/python

import sys
import os
os.environ['DJANGO_SETTINGS_MODULE']='fidoonline.settings'
sys.path.append('/media/FireTwo/FidoMembership')
import fidoonline.membermanage.models as models
import fidoonline.membermanage.reviewmodels as review

tuppr = models.Member.objects.get(pk=1)
types = tuppr.contactstatusText
zeros = [0]*len(types)
cnts  = dict(zip(types, zeros))
for mbr in models.Member.objects.all() :
    cnts[mbr.contactStatus] += 1
for key in cnts.keys() :
    print ("%s: %03d" % (key, cnts[key]))
