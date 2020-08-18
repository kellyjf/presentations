#!/usr/bin/python


import re
import os
import argparse
import database as db
from datetime import datetime as dt

global sess

me=re.compile("([0-9a-f]+)\-([0-9a-f]+)\s+([-rwxsp]+)\s+([0-9a-f]+)\s*([:0-9a-f]+)\s+(\d*)\s*(\S*)\s*$")
un=re.compile("[0-9a-f]+:name=(\S*)\s*$")
mm=re.compile("(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*$")
pr=re.compile("(\d+)\s+\(.+\)\s+([RSDZTW])\s+(\d+)\s+.*$")

def process_pid(pid):

	now = dt.now()
	proc=db.Process(pid=pid)
	proc.marktime=now

	with open("/proc/{}/cmdline".format(pid), "r") as f:
		cmd=f.read().replace('\x00',' ')
		print "PROC: ",pid,cmd
		proc.command=cmd

	with open("/proc/{}/cgroup".format(pid), "r") as f:
		for line in f:
			res=un.match(line)
			if res:
				proc.scope=res.group(1)

	with open("/proc/{}/statm".format(pid), "r") as f:
		for line in f:
			res=mm.match(line)
			if res:
				(size,rss,share,text,_,data,_)=res.groups()
				proc.marktime=now
				proc.size=size
				proc.rss=rss
				proc.share=share
				proc.text=text
				proc.data=data

	with open("/proc/{}/stat".format(pid), "r") as f:
		for line in f:
			res=pr.match(line)
			if res:
				(pid,state,ppid)=res.groups()
				proc.ppid=ppid

	sess.add(proc)

	with open("/proc/{}/maps".format(pid), "r") as f:
		for line in f:
			m=me.match(line)
			if m:
				(mapaddr,mapend,perms,offset,device,inode,name)=m.groups()
				maplen=int(mapend,16)-int(mapaddr,16)
				map=db.Mapping(mapaddr=mapaddr,
					mapend=mapend,
					maplen=maplen,
					perms=perms,
					offset=offset,
					device=device,
					inode=inode,
					filename=name,
					process=proc)	
				sess.add(map)



def report():

	if False:
		maps=sess.query(db.Mapping,db.func.sum(db.Mapping.maplen))\
		.filter(db.Mapping.perms.like('%w%'))\
		.group_by(db.Mapping.pid,db.Mapping.perms)\
		.order_by(db.func.sum(db.Mapping.maplen).desc())\
		.all()
	maps=sess.query(db.Mapping,db.func.sum(db.Mapping.maplen))\
		.filter(db.Mapping.perms.like('%w%p'))\
		.group_by(db.Mapping.pid)\
		.order_by(db.func.sum(db.Mapping.maplen).desc())\
		.all()

	for m in maps:
		if args.tabs:
			(mdat,pdat,sdat)=(m[0],m[0].process,m[1])
			print "\t".join([str(x) for x in [sdat,pdat.rss*4096,mdat.pid,mdat.perms,pdat.scope.split("/")[-1],pdat.rss,pdat.command]])
		else:
			print "WMEM {3:>12d} {2.pid:5d} {2.command:<35.35s} {2.scope:<35s} {1.perms} {2.rss}".format(m[0],m[0],m[0].process,m[1])

	maps=sess.query(db.func.sum(db.Mapping.maplen))\
		.filter(db.Mapping.perms.like('%w%p'))\
		.order_by(db.func.sum(db.Mapping.maplen).desc())\
		.all()
	for m in maps:
		print "WMEM:",m[0]
	maps=sess.query(db.func.sum(db.Process.rss))\
		.order_by(db.func.sum(db.Process.rss).desc())\
		.all()
	for m in maps:
		print "RSS:",4096*m[0]

if __name__ == "__main__":
	parser=argparse.ArgumentParser()
	parser.add_argument("--create", "-c", default=False, action="store_true")
	parser.add_argument("--report", "-r", default=False, action="store_true")
	parser.add_argument("--gather", "-g", default=False, action="store_true")
	parser.add_argument("--tabs", "-t", default=False, action="store_true")
	args=parser.parse_args()

	if args.create:
		db.create()

	sess=db.Session()

	if args.gather:
		pids=[x for x in os.listdir("/proc") if re.match("\d+",x)]
		for pid in pids:
			try:
				process_pid(pid)	
			except IOError :
				pass
	sess.commit()

	if args.report:
		report()

	
	print("Hello")


