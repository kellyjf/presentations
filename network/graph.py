#!/usr/bin/python

import argparse
import subprocess
import re
import os
import sqlite3 as sql


def database():
	conn=sql.connect("graph.sqlite")
	conn.row_factory=sql.Row
	cur=conn.cursor()
	res=cur.execute('''
		drop table if exists namespaces;
	''')
	res=cur.execute('''
		create table namespaces (
			id   integer primary key,
			nsname text );
	''')
	res=cur.execute('''
		drop table if exists interfaces;
	''')
	res=cur.execute('''
		create table interfaces (
			id          integer  primary key,
			ifid        integer,
			iflink      integer,
			nsname      text,
			ifname      text,
			basename    text,
			master      text,
			vid         integer,
			address     text );
	''')
	conn.commit()
	conn.close()

def loadns():
	conn=sql.connect("graph.sqlite")
	conn.row_factory=sql.Row
	cur=conn.cursor()
	
	# Load the namespaces
	p=subprocess.Popen("ip netns ls", shell=True, stdout=subprocess.PIPE)
	p.wait()
	lines=p.stdout.readlines()
	rx=re.compile("(\w+) \(id: (\d+)\).*")
	rn=re.compile("(\w+)$")
	for line in lines:
		print line
		if rx.match(line):
			name=rx.match(line).group(1)
			id=rx.match(line).group(2)
			cur.execute("insert into namespaces (id,nsname) values (?,?)",[id,name])
	for line in lines:
		if rn.match(line):
			name=rn.match(line).group(1)
			if name=="main":
				cur.execute("insert into namespaces (id,nsname) values (?,?)",[-1,name])
			else:
				cur.execute("insert into namespaces (nsname) values (?)",[name])
	conn.commit()
			
def loadifs():
	# Load the interfaces
	rb=re.compile("(\d+):\s*([\w\-]*):.* bridge .*$")
	rp=re.compile("(\d+):\s*([\w\-]+)@([\w\-]+):.* master (\w*) .* 802\.1Q id (\d+) .* bridge_slave .*$")
	rl=re.compile("(\d+):\s*([\w\-]+)@([\w\-]+):.* 802\.1Q id (\d+) .*$")
	rm=re.compile("(\d+):\s*([\w\-]+)@([\w\-]+): .*$")
	conn=sql.connect("graph.sqlite")
	conn.row_factory=sql.Row
	cur=conn.cursor()
	res=cur.execute("select nsname from namespaces")
	namespaces=res.fetchall()
	for namespace in namespaces:	
		ns=namespace['nsname']
		p=subprocess.Popen("ip netns exec {} ip -o -d link ls".format(ns), shell=True, stdout=subprocess.PIPE)
		p.wait()
		lines=p.stdout.readlines()
		for line in lines:
#			print ns,line
			ifname=None
			if rb.match(line):
				m=rb.match(line)
				print "bridge",m.groups()
				(ifid,ifname)=m.groups()
				cur.execute("insert into interfaces (ifid,nsname,ifname) "
					"values (?,?,?)",[ifid,ns,ifname])
			elif rp.match(line):
				m=rp.match(line)
				print "port",m.groups()
				(ifid,ifname,basename,master,vid)=m.groups()
				cur.execute("insert into interfaces (ifid,nsname,ifname,basename,master,vid) "
					"values (?,?,?,?,?,?)",[ifid,ns,ifname,basename,master,vid])
			elif rl.match(line):
				m=rl.match(line)
				print "link",m.groups()
				(ifid,ifname,basename,vid)=m.groups()
				cur.execute("insert into interfaces (ifid,nsname,ifname,basename,vid) "
					"values (?,?,?,?,?)",[ifid,ns,ifname,basename,vid])
			elif rm.match(line):
				m=rm.match(line)
				print "link",m.groups()
				(ifid,ifname,basename)=m.groups()
				cur.execute("insert into interfaces (ifid,nsname,ifname,basename) "
					"values (?,?,?,?)",[ifid,ns,ifname,basename])
			if ifname:
				p=subprocess.Popen("ip netns exec {} cat /sys/class/net/{}/iflink".format(ns,ifname), shell=True, stdout=subprocess.PIPE)
				p.wait()
				iflink=p.stdout.readline()
				cur.execute("update interfaces set iflink=? where nsname=? and ifname=?",
					[iflink, ns,ifname])
			
		p=subprocess.Popen("ip netns exec {} ip -4 -o  addr ls".format(ns), shell=True, stdout=subprocess.PIPE)
		p.wait()
		lines=p.stdout.readlines()
		ra=re.compile("(\d+):\s*([\-\w]+)\s+inet\s+([^ ]+)\s.*$")
		for line in lines:
			print ns,line
			if ra.match(line):
				m=ra.match(line)
				(ifid,ifname,addr)=m.groups()
				cur.execute("update interfaces set address=? where nsname=? and ifname=?",
					[addr, ns,ifname])
				print "addr",m.groups()
	conn.commit()
	return



if __name__ == "__main__":
	import signal
	signal.signal(signal.SIGINT, signal.SIG_DFL)

	parser=argparse.ArgumentParser()
	parser.add_option("c", "--create", action="store_true", help="Create database")
	args=parser.parse_args()
	if.create_
		os.unlink("network.sqlite")
		database()
		loadns()
		loadifs()
		
