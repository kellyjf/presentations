#!/usr/bin/python3


from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker,relationship
from sqlalchemy import create_engine, Column, Integer, String, Unicode, DateTime, ForeignKey, ForeignKeyConstraint, func


Base=declarative_base()
engine=create_engine("sqlite:///mmap.sqlite")
Session=sessionmaker(bind=engine)

class Process(Base):
	__tablename__ = "processes"

	marktime = Column(DateTime,primary_key=True)
	pid = Column(Integer, primary_key=True)
	ppid = Column(Integer)
	command  = Column(String)
	scope  = Column(String)
	size = Column(Integer)
	rss = Column(Integer)
	share = Column(Integer)
	text = Column(Integer)
	data = Column(Integer)
	minflt = Column(Integer)
	majflt = Column(Integer)
	nswap = Column(Integer)
	mappings = relationship("Mapping",back_populates='process')

class Mapping(Base):
	__tablename__ = "mappings"

	id = Column(Integer,primary_key=True)
	marktime = Column(DateTime)
	mapaddr  = Column(Integer)
	mapend  = Column(Integer)
	maplen  = Column(Integer)
	perms  = Column(String)
	offset  = Column(Integer)
	device  = Column(String)
	inode  = Column(Integer)
	filename  = Column(String)
	#pid = Column(Integer,ForeignKey("processes.pid"))
	pid = Column(Integer)
	process = relationship("Process",back_populates='mappings')
	__table_args__ = (ForeignKeyConstraint([marktime,pid],[Process.marktime,Process.pid]),{})


class Meminfo(Base):
	__tablename__ = "meminfos"

	id = Column(Integer,primary_key=True)
	marktime = Column(DateTime)
	key  = Column(String)
	value  = Column(Integer)

def create():
	Base.metadata.create_all(engine)

def report():
	heap=sess.query(db.Mapping,db.func.sum(db.Mapping.maplen)).filter(db.Mapping.filename=="").group_by(db.Mapping.pid,db.Mapping.perms).order_by(db.func.sum(db.Mapping.maplen).desc()).all()

	maps=sess.query(db.Mapping,db.func.sum(db.Mapping.maplen)).filter(db.Mapping.perms.like('%w%')).group_by(db.Mapping.pid,db.Mapping.perms).order_by(db.func.sum(db.Mapping.maplen).desc()).all()

if __name__ == "__main__":
	if args.create:
		create()

	s=Session()
	s.commit()
	
	print("Hello")


