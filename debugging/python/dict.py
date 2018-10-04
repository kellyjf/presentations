#!/usr/bin/python

import string
import md5
import signal
import pdb
import itertools

def handler(*args):
	pdb.set_trace()

signal.signal(signal.SIGUSR1, handler)

cnt=0
d=dict()
with open("/usr/share/dict/words","r") as f:
	for line in f:
		line.strip()
		perms=[[string.lower(x),string.upper(x)] for x in line]
		for trial in itertools.product(*perms):
			camel="".join(trial)
			if md5.new(camel).hexdigest()=="d827509c155e76332260e853537ca58a":
				print "Found it!",line,camel


