#!/usr/bin/python

import string

cnt=0
d=dict()
with open("/usr/share/dict/words","r") as f:
	for line in f:
		line.strip()
		d[cnt%1000]=line
		print line
		for i in range(1000):
			entry=d.get(i,"")
			if line==entry:
				print i,line,entry,line==entry


