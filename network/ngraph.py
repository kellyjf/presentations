#!/usr/bin/python

import argparse
import subprocess
import re
import os
import sys
import textwrap
import database as db


def loadns():
	sess=db.Session()
	# Load the namespaces
	p=subprocess.Popen("ip netns ls", shell=True, stdout=subprocess.PIPE)
	p.wait()
	lines=p.stdout.readlines()
	rx=re.compile("(\w+) \(id: (\d+)\).*")
	rn=re.compile("(\w+)$")
	for line in lines:
		print line
		if rx.match(line):
			(name,nsid)=rx.match(line).groups()
			sess.add(db.Namespace(nsname=name))
		elif rn.match(line):
			name=rn.match(line).group(1)
			sess.add(db.Namespace(nsname=name))
	sess.commit()
			
def loadifs():
	# Load the interfaces
	rb=re.compile("(\d+):\s*([\w\-]*):.* bridge .*$")
	rp=re.compile("(\d+):\s*([\w\-]+)@([\w\-]+):.* master (\w*) .* 802\.1Q id (\d+) .* bridge_slave .*$")
	rl=re.compile("(\d+):\s*([\w\-]+)@([\w\-]+):.* 802\.1Q id (\d+) .*$")
	rm=re.compile("(\d+):\s*([\w\-]+)@([\w\-]+): .*$")
	sess=db.Session()
	nslist=sess.query(db.Namespace)
	for nsobject in nslist:	
		ns=nsobject.nsname
		p=subprocess.Popen("ip netns exec {} ip -o -d link ls".format(ns), shell=True, stdout=subprocess.PIPE)
		p.wait()
		lines=p.stdout.readlines()
		for line in lines:
			print "NAMESPACE",ns,line
			ifid=None
			if rb.match(line):
				m=rb.match(line)
				print "bridge",m.groups()
				(ifid,ifname)=m.groups()
				sess.add(db.Interface(ifindex=ifid,nsname=ns,ifname=ifname))
			elif rp.match(line):
				m=rp.match(line)
				print "port",m.groups()
				(ifid,ifname,basename,master,vid)=m.groups()
				sess.add(db.Interface(ifindex=ifid,nsname=ns,ifname=ifname,
					basename=basename,master=master,vid=vid))
			elif rl.match(line):
				m=rl.match(line)
				print "link",m.groups()
				(ifid,ifname,basename,vid)=m.groups()
				sess.add(db.Interface(ifindex=ifid,nsname=ns,ifname=ifname,
					basename=basename,vid=vid))
			elif rm.match(line):
				m=rm.match(line)
				print "link",m.groups()
				(ifid,ifname,basename)=m.groups()
				sess.add(db.Interface(ifindex=ifid,nsname=ns,ifname=ifname,
					basename=basename))
			if ifid is not None:
				p=subprocess.Popen("ip netns exec {} cat /sys/class/net/{}/iflink".format(ns,ifname), shell=True, stdout=subprocess.PIPE)
				p.wait()
				iflink=p.stdout.readline()
				iface=sess.query(db.Interface).filter(db.Interface.ifindex==ifid).first()
				iface.iflink=iflink	
				sess.add(iface)
	
		p=subprocess.Popen("ip netns exec {} ip -4 -o  addr ls".format(ns), shell=True, stdout=subprocess.PIPE)
		p.wait()
		lines=p.stdout.readlines()
		ra=re.compile("(\d+):\s*([\-\w]+)\s+inet\s+([^ ]+)\s.*$")
		for line in lines:
			print ns,line
			if ra.match(line):
				m=ra.match(line)
				(ifid,ifname,addr)=m.groups()
				iface=sess.query(db.Interface)\
					.filter(db.Interface.nsname==ns)\
					.filter(db.Interface.ifname==ifname)\
					.first()
				# the lo interface doesn't get inserted
				if iface:
					iface.address=addr
					sess.add(iface)
				print "addr",m.groups()
	sess.commit()
	return


def draw(node,edge,**kwargs):
	format=kwargs.get('type', "jpg")
	number=kwargs.get('number', 0)
	info=kwargs.get('info', "")
	address=kwargs.get('address', "")
	proto=kwargs.get('proto', "")
	hotvid=kwargs.get('vid', 0)
	out=list()
	ilist=textwrap.wrap(info,25)[:2]
	ltxt="\\n".join(ilist)
	out.append( "digraph network {")
	if int(number):
		out.append( "label=\"Packet %6d\\n%s\\n%s\";"%(int(number),address,ltxt))

	for name,label in node.items():
		out.append( "%s %s;"%(name,label) )
	for vid,edict in edge.items():
		color="black"
		elabel=str(vid)
		if vid==int(hotvid):
			color="red"
			elabel=str(proto)
		out.append("%s->%s [dir=none, label=\"%s\", color=%s];"%(edict['wan'],edict['lan'],elabel,color))
	out.append("}")
	d=subprocess.Popen("dot -T %s -o %06d.%s"%(format,int(number),format), shell=True, stdin=subprocess.PIPE)
	d.stdin.write("\n".join(out))
	d.stdin.close()
	d.wait()

	if args.output:
		os.rename( "%06d.%s"%(int(number),format), args.output)
	if args.dotfile:
		if args.dotfile=="-":
			sys.stdout.write("\n".join(out))
		else:
			with open(args.dotfile,"w") as f:
				f.write("\n".join(out))

if __name__ == "__main__":
	import signal
	signal.signal(signal.SIGINT, signal.SIG_DFL)

	parser=argparse.ArgumentParser()
	parser.add_argument("-c", "--create", action="store_true")
	parser.add_argument("-p", "--pcap", help="Use a pcap file for annotation")
	parser.add_argument("-o", "--output", help="Name of output file")
	parser.add_argument("-t", "--type", choices=['jpg', 'pdf'], default='jpg', help="Output file format")
	parser.add_argument("-f", "--dotfile", help="Name of dot output file")
	args=parser.parse_args()
	if args.create:
		os.unlink("network.sqlite")
		db.create()
		loadns()
		loadifs()

	sess=db.Session()
	lan=sess.query(db.Interface).filter(db.Interface.ifname=="lan")\
		.filter(db.Interface.nsname=="main").first()
	nss=sess.query(db.Namespace).filter(db.Namespace.nsname != "main")
	nss=sess.query(db.Namespace)

	node=dict()
	edge=dict()

	for ns in nss:
		lanifs=sess.query(db.Interface).filter(db.Interface.namespace==ns)\
			.filter(db.Interface.iflink==lan.ifindex)\
			.filter(db.Interface.ifname!="lan")
		#print "LAN",[(x.nsname,x.ifname,x.address) for x in lanifs]	

		wanifs=sess.query(db.Interface).filter(db.Interface.namespace==ns)\
			.filter(db.Interface.iflink==lan.iflink)\
			.filter(db.Interface.ifname!="lan")\
			.filter(db.Interface.master==None)
		#print "WAN",[(x.nsname,x.ifname,x.address) for x in wanifs]	

		brifs=sess.query(db.Interface).filter(db.Interface.namespace==ns)\
			.filter(db.Interface.ifindex==db.Interface.iflink)\
			.filter(db.Interface.nsname!="main")
		#print "BR",[(x.nsname,x.ifname,x.address) for x in brifs]	

		portifs=sess.query(db.Interface).filter(db.Interface.namespace==ns)\
			.filter(db.Interface.master!=None)
		#print "PORT",[(x.nsname,x.ifname) for x in portifs]	

		lanl="|".join(["<%s>%s"%(x.ifname,x.address) for x in lanifs])
		wanl="|".join(["<%s>%s"%(x.ifname,x.address) for x in wanifs])
		brl="|".join(["<%s>%s\\n%s"%(x.ifname,x.ifname,x.address) for x in brifs])
		if brl:
			brl="|"+brl+"|"
		lbl=" {%s} | %s" %(lanl,ns.nsname)
		if wanl or brl:
			lbl+="| {%s %s} "%(wanl,brl)
 
		# node is a dict that maps nsname to the dotty node spec
		node[str(ns.nsname)]="[shape=record,label=\"{ %s } \"]"%(lbl)

		# edge maps VIDs to a dict with wan, lan dotty connection points (node:port)
		# the VID will normally be the label, but we can override it if processing
		# a pcap file
		for link in wanifs:
			edge[link.vid]= { 
				'wan':"%s:%s"%(
					ns.nsname,link.ifname
				),
				'lan':"%s:%s"%(
					link.ifname,ns.nsname
				)}
		for port in portifs:
			edge[port.vid]= { 
				'wan':"%s:%s"%(
					ns.nsname,port.master
				),
				'lan':"%s:%s"%(
					port.ifname,ns.nsname
				)}
			
	if args.pcap:
		p=subprocess.Popen("tshark -r {} -Y vlan.id -T fields -E separator=/t -e frame.number -e vlan.id -e ip.addr -e col.Protocol -e col.Info".format(args.pcap), shell=True, stdout=subprocess.PIPE)
		p.wait()
		lines=p.stdout.readlines()

		for  line in lines:
			line=line[:-1]
			(num,vid,addr,proto,info)=line.split("\t")
			draw(node,edge,type=args.type,number=num,address=addr,info=info,vid=vid,proto=proto)
	else:
		draw(node,edge,type=args.type)
