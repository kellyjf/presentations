#!/usr/bin/python

import socket
import argparse
import time
import threading

class Client(threading.Thread):
	def __init__(self, sock):
		self.sock=sock
	def run(self):
		cnt=0
		while True:
			if args.payload:
				try:
					cnt+=1
					print "SRV", cnt
					self.sock.send('s'*args.payload)
				except:
					return
#			try:
#				self.sock.recv(args.payload)
#			except Exception as e:
#				return
			if args.delay:
				time.sleep(args.delay)


def run_server():
	s=socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.getprotobyname("tcp"))
	s.bind((args.server, args.port))
	s.listen(args.listen)
	while True:
		(c,addr)=s.accept()
		cthread=Client(c)
		cthread.run()

def run_client():
	s=socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.getprotobyname("tcp"))
	s.connect((args.server, args.port))
	cnt=0
	while True:
#		if args.payload:
#			s.send('c'*args.payload)
		cnt+=1
		print "CLN", cnt
		s.recv(args.payload)
		if args.delay:
			time.sleep(args.delay)

if __name__ == "__main__":
	parser=argparse.ArgumentParser()
	parser.add_argument( "server", nargs='?', default="127.0.0.1")
	parser.add_argument( "port",  nargs='?', type=int, default=5555)
	parser.add_argument("--listen", "-l", type=int, default=0)
	parser.add_argument("--delay", "-d", type=int, default=0)
	parser.add_argument("--payload", "-p", type=int, default=1500)

	args=parser.parse_args()

	if args.listen:
		run_server()
	else:
		run_client()
