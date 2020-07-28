#!/usr/bin/python


import re
import os
import argparse
import database as db

global sess

def process_pid(pid):
	me=re.compile("([0-9a-f]+)\-([0-9a-f]+)\s+([-rwxp]+)\s+([0-9a-f]+)\s*([:0-9a-f]+)\s+(\d*)\s*(\S*)\s*$")
	with open("/proc/{}/cmdline".format(pid), "r") as f:
		cmd=f.read().replace('\x00',' ')
		proc=db.Process(id=pid,command=cmd)
		print "PROC: ",pid,cmd
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
	heap=sess.query(db.Mapping,db.func.sum(db.Mapping.maplen)).filter(db.Mapping.device=="00:00").group_by(db.Mapping.pid,db.Mapping.perms).order_by(db.func.sum(db.Mapping.maplen).desc()).all()

	for m in heap:
		print "HEAP {2} {1:>12d} {0}".format(m[0].process.command,m[1],m[0].perms)

	maps=sess.query(db.Mapping,db.func.sum(db.Mapping.maplen)).filter(db.Mapping.perms.like('%w%')).group_by(db.Mapping.pid,db.Mapping.perms).order_by(db.func.sum(db.Mapping.maplen).desc()).all()

	for m in maps:
		print "MAP  {1:>12d} {0:<20s} {2}".format(m[0].process.command,m[1],m[0].filename)
if __name__ == "__main__":
	parser=argparse.ArgumentParser()
	parser.add_argument("--create", "-c", default=False, action="store_true")
	parser.add_argument("--report", "-r", default=False, action="store_true")
	parser.add_argument("--gather", "-g", default=False, action="store_true")
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

	if args.report:
		report()

	sess.commit()
	
	print("Hello")


