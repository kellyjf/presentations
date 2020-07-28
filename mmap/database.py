#!/usr/bin/python3


from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker,relationship
from sqlalchemy import create_engine, Column, Integer, String, Unicode, DateTime, ForeignKey, func


Base=declarative_base()
engine=create_engine("sqlite:///mmap.sqlite")
Session=sessionmaker(bind=engine)

class Mapping(Base):
	__tablename__ = "mappings"

	id = Column(Integer,primary_key=True)
	mapaddr  = Column(Integer)
	mapend  = Column(Integer)
	maplen  = Column(Integer)
	perms  = Column(String)
	offset  = Column(Integer)
	device  = Column(String)
	inode  = Column(Integer)
	filename  = Column(String)
	pid = Column(Integer,ForeignKey("processes.id"))
	process = relationship("Process",back_populates='mappings')

class Process(Base):
	__tablename__ = "processes"

	id = Column(Integer, primary_key=True)
	command  = Column(String)
	mappings = relationship("Mapping",back_populates='process')

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


